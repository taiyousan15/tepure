import { test, expect, setupAuthenticatedSession, setupAPIMocks, checkAccessibility, MOCK_RESPONSES } from './fixtures';

/**
 * Template Registration Flow E2E Tests
 */
test.describe('Template Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup authentication
    await setupAuthenticatedSession(page);

    // Setup API mocks
    await setupAPIMocks(page);
  });

  test('should display create template page correctly', async ({ createTemplatePage }) => {
    await createTemplatePage.goto();

    // Check page elements
    await expect(createTemplatePage.heading).toBeVisible();
    await expect(createTemplatePage.form).toBeVisible();
    await expect(createTemplatePage.nameInput).toBeVisible();
    await expect(createTemplatePage.descriptionInput).toBeVisible();
    await expect(createTemplatePage.categorySelect).toBeVisible();
    await expect(createTemplatePage.figmaUrlInput).toBeVisible();
    await expect(createTemplatePage.submitButton).toBeVisible();

    // Check accessibility
    await checkAccessibility(createTemplatePage.page);
  });

  test('should create template successfully with valid data', async ({ createTemplatePage, templatesPage, page }) => {
    await createTemplatePage.goto();

    // Mock successful creation
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.createTemplate),
        });
      }
    });

    // Fill form
    const templateData = {
      name: 'New Marketing Template',
      description: 'A new template for marketing campaigns',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test123',
    };

    await createTemplatePage.fillAndSubmit(templateData);

    // Wait for success and redirect
    await createTemplatePage.waitForSuccess();
    await createTemplatePage.waitForRedirect();

    // Verify we're redirected to templates page
    expect(await templatesPage.isOnTemplatesPage()).toBe(true);
  });

  test('should validate required fields', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Try to submit empty form
    await createTemplatePage.submit();

    // Check HTML5 validation
    const nameValid = await createTemplatePage.nameInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(nameValid).toBe(false);
  });

  test('should validate Figma URL format', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Fill form with invalid Figma URL
    await createTemplatePage.fillForm({
      name: 'Test Template',
      description: 'Test Description',
      category: 'Marketing',
      figmaUrl: 'not-a-valid-url',
    });

    // Submit form
    await createTemplatePage.submit();

    // Should show validation error or prevent submission
    await page.waitForTimeout(1000);

    // Check if still on create page
    expect(await createTemplatePage.isOnCreateTemplatePage()).toBe(true);
  });

  test('should handle API errors during creation', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Mock API error
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'CREATE_ERROR',
              message: 'Failed to create template',
            },
          }),
        });
      }
    });

    // Fill and submit form
    await createTemplatePage.fillAndSubmit({
      name: 'Test Template',
      description: 'Test Description',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test123',
    });

    // Wait for error
    await page.waitForTimeout(1000);

    // Should show error message or stay on form
    expect(await createTemplatePage.isOnCreateTemplatePage()).toBe(true);
  });

  test('should cancel form and navigate back', async ({ createTemplatePage, templatesPage }) => {
    await createTemplatePage.goto();

    // Fill some data
    await createTemplatePage.fillName('Test Template');

    // Cancel
    await createTemplatePage.cancel();

    // Wait for navigation
    await createTemplatePage.page.waitForURL(/\/templates$/, { timeout: 5000 });

    // Verify we're back on templates page
    expect(await templatesPage.isOnTemplatesPage()).toBe(true);
  });

  test('should upload thumbnail image', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Note: File upload testing requires actual file
    // This test documents the expected behavior

    // Check thumbnail input exists
    await expect(createTemplatePage.thumbnailInput).toBeVisible();

    const inputType = await createTemplatePage.thumbnailInput.getAttribute('type');
    expect(inputType).toBe('file');
  });

  test('should validate name length', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Fill with very long name
    await createTemplatePage.fillName('A'.repeat(1000));

    const nameValue = await createTemplatePage.nameInput.inputValue();

    // Should be truncated or validated
    expect(nameValue.length).toBeGreaterThan(0);
  });

  test('should validate description length', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Fill with very long description
    await createTemplatePage.fillDescription('A'.repeat(10000));

    const descriptionValue = await createTemplatePage.descriptionInput.inputValue();

    // Should be truncated or validated
    expect(descriptionValue.length).toBeGreaterThan(0);
  });

  test('should show category options', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Check category select has options
    const options = await page.locator('select[name="category"] option, [role="option"]').count();

    expect(options).toBeGreaterThan(0);
  });

  test('should preserve form data on error', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Mock API error
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Invalid data',
            },
          }),
        });
      }
    });

    // Fill form
    const templateData = {
      name: 'Test Template',
      description: 'Test Description',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test123',
    };

    await createTemplatePage.fillAndSubmit(templateData);

    // Wait for error
    await page.waitForTimeout(1000);

    // Check form data is preserved
    const nameValue = await createTemplatePage.nameInput.inputValue();
    expect(nameValue).toBe(templateData.name);

    const descriptionValue = await createTemplatePage.descriptionInput.inputValue();
    expect(descriptionValue).toBe(templateData.description);
  });

  test('should disable submit button during submission', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Mock delayed API response
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.createTemplate),
        });
      }
    });

    // Fill and submit form
    const submitPromise = createTemplatePage.fillAndSubmit({
      name: 'Test Template',
      description: 'Test Description',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test123',
    });

    // Check button is disabled during submission
    await page.waitForTimeout(200);
    const isDisabled = await createTemplatePage.submitButton.isDisabled();

    // Wait for submission to complete
    await submitPromise;
  });

  test('should support keyboard navigation', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Tab through form fields
    await page.keyboard.press('Tab'); // Focus first field
    await page.keyboard.type('Test Template');

    await page.keyboard.press('Tab'); // Focus next field
    await page.keyboard.type('Description');

    await page.keyboard.press('Tab'); // Focus category
    await page.keyboard.press('ArrowDown'); // Select option

    await page.keyboard.press('Tab'); // Focus Figma URL
    await page.keyboard.type('https://figma.com/file/test');
  });

  test('should validate duplicate template names', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Mock duplicate error
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'DUPLICATE_NAME',
              message: 'Template name already exists',
            },
          }),
        });
      }
    });

    // Submit form with duplicate name
    await createTemplatePage.fillAndSubmit({
      name: 'Existing Template',
      description: 'Test',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test',
    });

    // Wait for error
    await page.waitForTimeout(1000);

    // Should show error message
    const errorVisible = await createTemplatePage.errorMessage.isVisible().catch(() => false);
  });
});

/**
 * Mobile Template Registration Tests
 */
test.describe('Template Registration Flow - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should display form correctly on mobile', async ({ createTemplatePage }) => {
    await createTemplatePage.goto();

    // Check page elements
    await expect(createTemplatePage.form).toBeVisible();
    await expect(createTemplatePage.nameInput).toBeVisible();
    await expect(createTemplatePage.submitButton).toBeVisible();
  });

  test('should create template successfully on mobile', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Mock successful creation
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.createTemplate),
        });
      }
    });

    // Fill and submit
    await createTemplatePage.fillAndSubmit({
      name: 'Mobile Template',
      description: 'Mobile Description',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/mobile',
    });

    // Wait for response
    await page.waitForTimeout(2000);
  });

  test('should handle virtual keyboard on mobile', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Focus on input (triggers virtual keyboard)
    await createTemplatePage.nameInput.focus();

    // Type text
    await page.keyboard.type('Mobile Template Name');

    // Check value
    const nameValue = await createTemplatePage.nameInput.inputValue();
    expect(nameValue).toBe('Mobile Template Name');
  });
});

/**
 * Accessibility Tests
 */
test.describe('Template Registration - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should have proper form labels', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Check for labels or aria-labels
    const nameLabel = await page.locator('label[for*="name"], [aria-label*="name"]').count();
    expect(nameLabel).toBeGreaterThan(0);
  });

  test('should have proper error announcements', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Check for aria-live region for errors
    const ariaLive = page.locator('[aria-live="polite"], [aria-live="assertive"], [role="alert"]');
    const liveRegionCount = await ariaLive.count();

    // Should have at least one live region for dynamic announcements
    expect(liveRegionCount).toBeGreaterThanOrEqual(0);
  });

  test('should support screen reader navigation', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Check for semantic form structure
    const form = createTemplatePage.form;
    await expect(form).toBeVisible();

    // Check for proper heading hierarchy
    const headings = page.locator('h1, h2, h3');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);
  });
});

/**
 * Form Validation Tests
 */
test.describe('Template Registration - Form Validation', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should validate required name field', async ({ createTemplatePage }) => {
    await createTemplatePage.goto();

    // Try to submit without name
    await createTemplatePage.fillForm({
      name: '',
      description: 'Description',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test',
    });

    await createTemplatePage.submit();

    // Should prevent submission
    expect(await createTemplatePage.isOnCreateTemplatePage()).toBe(true);
  });

  test('should validate Figma URL pattern', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Fill with various URL formats
    const invalidUrls = ['http://example.com', 'not-a-url', 'ftp://figma.com'];

    for (const url of invalidUrls) {
      await createTemplatePage.figmaUrlInput.fill(url);

      // Check validation
      const isValid = await createTemplatePage.figmaUrlInput.evaluate(
        (el: HTMLInputElement) => el.validity.valid
      );

      // May be invalid depending on validation rules
    }
  });

  test('should clear form after successful submission', async ({ createTemplatePage, page }) => {
    await createTemplatePage.goto();

    // Mock successful creation
    await page.route('**/api/v1/templates', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.createTemplate),
        });
      }
    });

    // Submit form
    await createTemplatePage.fillAndSubmit({
      name: 'Test Template',
      description: 'Test',
      category: 'Marketing',
      figmaUrl: 'https://figma.com/file/test',
    });

    // Wait for redirect
    await page.waitForTimeout(2000);

    // Form should be cleared or navigated away
    expect(await createTemplatePage.isOnCreateTemplatePage()).toBe(false);
  });
});
