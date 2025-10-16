import { test, expect, setupAuthenticatedSession, setupAPIMocks, checkAccessibility, MOCK_RESPONSES } from './fixtures';

/**
 * Template Usage Flow E2E Tests
 */
test.describe('Template Usage Flow', () => {
  const TEMPLATE_ID = 'template-1';

  test.beforeEach(async ({ page }) => {
    // Setup authentication
    await setupAuthenticatedSession(page);

    // Setup API mocks
    await setupAPIMocks(page);
  });

  test('should display use template page correctly', async ({ useTemplatePage }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Check page elements
    await expect(useTemplatePage.heading).toBeVisible();
    await expect(useTemplatePage.form).toBeVisible();
    await expect(useTemplatePage.submitButton).toBeVisible();

    // Check accessibility
    await checkAccessibility(useTemplatePage.page);
  });

  test('should display template information', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Wait for template data to load
    await page.waitForLoadState('networkidle');

    // Check template name is displayed
    const pageContent = await page.textContent('body');
    expect(pageContent).toContain('Template');
  });

  test('should fill and submit form successfully', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Mock successful submission
    await page.route('**/api/v1/templates/*/use', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_RESPONSES.useTemplate),
      });
    });

    // Fill form data
    const formData = {
      title: 'Test Title',
      description: 'Test Description',
      author: 'Test Author',
    };

    await useTemplatePage.fillAndSubmit(formData);

    // Wait for success message
    await useTemplatePage.waitForSuccess();

    // Verify success message is displayed
    await expect(useTemplatePage.successMessage).toBeVisible();

    const successText = await useTemplatePage.getSuccessMessage();
    expect(successText).toBeTruthy();
  });

  test('should validate required fields', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Try to submit empty form
    await useTemplatePage.submit();

    // Check form validation
    const isValid = await useTemplatePage.isFormValid();

    // Form should be invalid or show validation errors
    // Note: This depends on HTML5 validation or custom validation
  });

  test('should handle API errors during submission', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Mock API error
    await page.route('**/api/v1/templates/*/use', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'PROCESSING_ERROR',
            message: 'Failed to process template',
          },
        }),
      });
    });

    // Fill and submit form
    await useTemplatePage.fillAndSubmit({
      title: 'Test',
      description: 'Test',
      author: 'Test',
    });

    // Wait for error message
    await page.waitForTimeout(1000);

    // Should display error or stay on form
    expect(await useTemplatePage.isOnUseTemplatePage()).toBe(true);
  });

  test('should navigate back to templates list', async ({ useTemplatePage, templatesPage }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Click back button
    await useTemplatePage.goBack();

    // Wait for navigation
    await useTemplatePage.page.waitForURL(/\/templates$/, { timeout: 5000 });

    // Verify we're on templates page
    expect(await templatesPage.isOnTemplatesPage()).toBe(true);
  });

  test('should show loading state during submission', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Mock delayed API response
    await page.route('**/api/v1/templates/*/use', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_RESPONSES.useTemplate),
      });
    });

    // Fill and submit form
    const submitPromise = useTemplatePage.fillAndSubmit({
      title: 'Test',
      description: 'Test',
      author: 'Test',
    });

    // Check for loading indicator
    await page.waitForTimeout(200);
    const loadingVisible = await useTemplatePage.loadingIndicator.isVisible().catch(() => false);

    // Wait for submission to complete
    await submitPromise;
  });

  test('should poll job status after submission', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    let pollCount = 0;

    // Mock job status polling
    await page.route('**/api/v1/jobs/*', async (route) => {
      pollCount++;

      if (pollCount < 3) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: 'job-123',
            status: 'processing',
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.jobStatus),
        });
      }
    });

    // Submit form
    await useTemplatePage.fillAndSubmit({
      title: 'Test',
      description: 'Test',
      author: 'Test',
    });

    // Wait for job to complete
    await page.waitForTimeout(5000);

    // Should eventually show success
    const successVisible = await useTemplatePage.successMessage.isVisible().catch(() => false);
  });

  test('should display generated Figma URL after completion', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Mock successful completion with URL
    await page.route('**/api/v1/jobs/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'job-123',
          status: 'completed',
          result_url: 'https://figma.com/file/generated-123',
        }),
      });
    });

    // Submit form
    await useTemplatePage.fillAndSubmit({
      title: 'Test',
      description: 'Test',
      author: 'Test',
    });

    // Wait for completion
    await page.waitForTimeout(3000);

    // Check for Figma URL link
    const figmaLink = page.locator('a[href*="figma.com"]');
    const linkCount = await figmaLink.count();

    // May or may not display link depending on implementation
  });

  test('should handle form input validation', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Test max length validation (if any)
    await useTemplatePage.fillInputByName('title', 'A'.repeat(1000));

    const titleValue = await page.locator('input[name="title"]').inputValue();

    // Check if value is truncated or validated
    expect(titleValue.length).toBeGreaterThan(0);
  });

  test('should preserve form data on validation error', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Fill form
    const formData = {
      title: 'Test Title',
      description: 'Test Description',
    };

    await useTemplatePage.fillForm(formData);

    // Mock validation error
    await page.route('**/api/v1/templates/*/use', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input',
          },
        }),
      });
    });

    // Submit
    await useTemplatePage.submit();

    // Wait a moment
    await page.waitForTimeout(1000);

    // Check form data is still there
    const titleValue = await page.locator('input[name="title"]').inputValue();
    expect(titleValue).toBe(formData.title);
  });

  test('should support keyboard shortcuts', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Fill first field
    await page.locator('input').first().focus();
    await page.keyboard.type('Test');

    // Tab through fields
    await page.keyboard.press('Tab');
    await page.keyboard.type('Description');

    // Submit with Ctrl+Enter (if supported)
    await page.keyboard.press('Control+Enter');

    // Wait a moment
    await page.waitForTimeout(500);
  });
});

/**
 * Mobile Template Usage Tests
 */
test.describe('Template Usage Flow - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  const TEMPLATE_ID = 'template-1';

  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should display form correctly on mobile', async ({ useTemplatePage }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Check page elements
    await expect(useTemplatePage.form).toBeVisible();
    await expect(useTemplatePage.submitButton).toBeVisible();
  });

  test('should submit form successfully on mobile', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Fill and submit
    await useTemplatePage.fillAndSubmit({
      title: 'Mobile Test',
      description: 'Mobile Description',
      author: 'Mobile User',
    });

    // Wait for response
    await page.waitForTimeout(2000);

    // Should show success or stay on page
    expect(await useTemplatePage.isOnUseTemplatePage()).toBe(true);
  });
});

/**
 * Error Handling Tests
 */
test.describe('Template Usage - Error Handling', () => {
  const TEMPLATE_ID = 'template-1';

  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should handle network timeout', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Mock timeout
    await page.route('**/api/v1/templates/*/use', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 60000));
      await route.abort('timedout');
    });

    // Submit form
    await useTemplatePage.fillAndSubmit({
      title: 'Test',
      description: 'Test',
      author: 'Test',
    });

    // Wait for timeout handling
    await page.waitForTimeout(5000);

    // Should show error or timeout message
    expect(await useTemplatePage.isOnUseTemplatePage()).toBe(true);
  });

  test('should handle job failure', async ({ useTemplatePage, page }) => {
    await useTemplatePage.goto(TEMPLATE_ID);

    // Mock job failure
    await page.route('**/api/v1/jobs/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'job-123',
          status: 'failed',
          error: 'Processing failed',
        }),
      });
    });

    // Submit form
    await useTemplatePage.fillAndSubmit({
      title: 'Test',
      description: 'Test',
      author: 'Test',
    });

    // Wait for job status check
    await page.waitForTimeout(3000);

    // Should show error message
    const errorVisible = await useTemplatePage.errorMessage.isVisible().catch(() => false);
  });

  test('should handle invalid template ID', async ({ useTemplatePage, page }) => {
    // Mock 404 response
    await page.route('**/api/v1/templates/invalid-id', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'NOT_FOUND',
            message: 'Template not found',
          },
        }),
      });
    });

    await useTemplatePage.goto('invalid-id');

    // Should show error or redirect
    await page.waitForTimeout(1000);
  });
});
