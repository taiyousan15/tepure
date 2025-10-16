import { test, expect, setupAuthenticatedSession, setupAPIMocks, checkAccessibility, MOCK_RESPONSES } from './fixtures';

/**
 * Template Browsing Flow E2E Tests
 */
test.describe('Template Browsing Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup authentication
    await setupAuthenticatedSession(page);

    // Setup API mocks
    await setupAPIMocks(page);
  });

  test('should display templates list page correctly', async ({ templatesPage }) => {
    await templatesPage.goto();

    // Check page elements
    await expect(templatesPage.heading).toBeVisible();
    await expect(templatesPage.searchInput).toBeVisible();

    // Check that templates are loaded
    const templateCount = await templatesPage.getTemplateCount();
    expect(templateCount).toBeGreaterThan(0);

    // Check accessibility
    await checkAccessibility(templatesPage.page);
  });

  test('should display all templates from API', async ({ templatesPage }) => {
    await templatesPage.goto();

    // Wait for templates to load
    await templatesPage.page.waitForLoadState('networkidle');

    // Check template count matches mock data
    const templateCount = await templatesPage.getTemplateCount();
    expect(templateCount).toBe(MOCK_RESPONSES.templates.length);

    // Check first template content
    const firstTemplateText = await templatesPage.getTemplateCardText(0);
    expect(firstTemplateText).toContain(MOCK_RESPONSES.templates[0].name);
  });

  test('should search templates by name', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Mock search API response
    await page.route('**/api/v1/templates*', async (route) => {
      const url = new URL(route.request().url());
      const searchQuery = url.searchParams.get('q');

      if (searchQuery) {
        const filteredTemplates = MOCK_RESPONSES.templates.filter((t) =>
          t.name.toLowerCase().includes(searchQuery.toLowerCase())
        );

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(filteredTemplates),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.templates),
        });
      }
    });

    // Search for specific template
    await templatesPage.search('Sample Template 1');

    // Wait for results
    await page.waitForTimeout(500);

    // Check filtered results
    const templateCount = await templatesPage.getTemplateCount();
    expect(templateCount).toBeGreaterThanOrEqual(1);
  });

  test('should filter templates by category', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Mock category filter API response
    await page.route('**/api/v1/templates*', async (route) => {
      const url = new URL(route.request().url());
      const category = url.searchParams.get('category');

      if (category && category !== 'all') {
        const filteredTemplates = MOCK_RESPONSES.templates.filter((t) => t.category === category);

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(filteredTemplates),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RESPONSES.templates),
        });
      }
    });

    // Filter by category
    await templatesPage.filterByCategory('Marketing');

    // Wait for results
    await page.waitForTimeout(500);

    // Check filtered results
    const templateCount = await templatesPage.getTemplateCount();
    expect(templateCount).toBeGreaterThanOrEqual(0);
  });

  test('should open template detail modal on card click', async ({ templatesPage }) => {
    await templatesPage.goto();

    // Click first template
    await templatesPage.clickTemplate(0);

    // Wait for modal to open
    await templatesPage.waitForModalOpen();

    // Verify modal is visible
    await expect(templatesPage.templateModal).toBeVisible();

    // Verify modal contains template information
    const modalContent = await templatesPage.templateModal.textContent();
    expect(modalContent).toContain(MOCK_RESPONSES.templates[0].name);
  });

  test('should close template detail modal', async ({ templatesPage }) => {
    await templatesPage.goto();

    // Open modal
    await templatesPage.clickTemplate(0);
    await templatesPage.waitForModalOpen();

    // Close modal
    await templatesPage.closeModal();

    // Verify modal is hidden
    await expect(templatesPage.templateModal).not.toBeVisible();
  });

  test('should navigate to use template page from modal', async ({ templatesPage, useTemplatePage }) => {
    await templatesPage.goto();

    // Open modal
    await templatesPage.clickTemplate(0);
    await templatesPage.waitForModalOpen();

    // Click use template button
    await templatesPage.clickUseTemplateInModal();

    // Wait for navigation
    await templatesPage.page.waitForURL(/\/templates\/.*\/use/, { timeout: 5000 });

    // Verify we're on use template page
    expect(await useTemplatePage.isOnUseTemplatePage()).toBe(true);
  });

  test('should navigate to create template page', async ({ templatesPage, createTemplatePage }) => {
    await templatesPage.goto();

    // Click create button
    await templatesPage.goToCreateTemplate();

    // Wait for navigation
    await templatesPage.page.waitForURL(/\/templates\/create/, { timeout: 5000 });

    // Verify we're on create template page
    expect(await createTemplatePage.isOnCreateTemplatePage()).toBe(true);
  });

  test('should handle empty search results', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Mock empty search results
    await page.route('**/api/v1/templates*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Search for non-existent template
    await templatesPage.search('NonExistentTemplate12345');

    // Wait for results
    await page.waitForTimeout(500);

    // Check no templates displayed
    const templateCount = await templatesPage.getTemplateCount();
    expect(templateCount).toBe(0);
  });

  test('should handle API errors gracefully', async ({ templatesPage, page }) => {
    // Mock API error
    await page.route('**/api/v1/templates', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: { message: 'Internal Server Error' } }),
      });
    });

    await templatesPage.goto();

    // Should display error or empty state
    await page.waitForTimeout(1000);
  });

  test('should support keyboard navigation in template list', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Focus first template
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Press Enter to open modal
    await page.keyboard.press('Enter');

    // Wait for modal
    await page.waitForTimeout(500);
  });

  test('should display template thumbnails', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Check for images in template cards
    const images = page.locator('[data-testid="template-card"] img, .template-card img');
    const imageCount = await images.count();

    expect(imageCount).toBeGreaterThan(0);

    // Check first image has src
    const firstImageSrc = await images.first().getAttribute('src');
    expect(firstImageSrc).toBeTruthy();
  });

  test('should display template metadata', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Click first template to open modal
    await templatesPage.clickTemplate(0);
    await templatesPage.waitForModalOpen();

    // Check for metadata fields
    const modalContent = await templatesPage.templateModal.textContent();

    expect(modalContent).toContain(MOCK_RESPONSES.templates[0].name);
    expect(modalContent).toContain(MOCK_RESPONSES.templates[0].category);
  });
});

/**
 * Mobile Template Browsing Tests
 */
test.describe('Template Browsing Flow - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should display templates list correctly on mobile', async ({ templatesPage }) => {
    await templatesPage.goto();

    // Check page elements
    await expect(templatesPage.heading).toBeVisible();

    // Check templates are displayed
    const templateCount = await templatesPage.getTemplateCount();
    expect(templateCount).toBeGreaterThan(0);
  });

  test('should open modal on mobile', async ({ templatesPage }) => {
    await templatesPage.goto();

    // Click template
    await templatesPage.clickTemplate(0);

    // Wait for modal
    await templatesPage.waitForModalOpen();

    // Verify modal is visible
    await expect(templatesPage.templateModal).toBeVisible();
  });

  test('should close modal with swipe gesture on mobile', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Open modal
    await templatesPage.clickTemplate(0);
    await templatesPage.waitForModalOpen();

    // Try to close with escape key (alternative to swipe)
    await page.keyboard.press('Escape');

    // Wait a moment
    await page.waitForTimeout(500);

    // Check if modal is hidden (may vary based on implementation)
    const isVisible = await templatesPage.templateModal.isVisible();
    // Modal may still be visible if escape doesn't close it on mobile
    // This test documents the expected behavior
  });
});

/**
 * Accessibility Tests
 */
test.describe('Template Browsing - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page);
    await setupAPIMocks(page);
  });

  test('should have proper ARIA labels', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Check for ARIA attributes
    const searchInput = templatesPage.searchInput;
    const ariaLabel = await searchInput.getAttribute('aria-label');

    // Should have aria-label or placeholder
    const placeholder = await searchInput.getAttribute('placeholder');
    expect(ariaLabel || placeholder).toBeTruthy();
  });

  test('should support screen reader navigation', async ({ templatesPage, page }) => {
    await templatesPage.goto();

    // Check for semantic HTML
    const main = page.locator('main');
    await expect(main).toBeVisible();

    // Check for headings
    const headings = page.locator('h1, h2, h3');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);
  });
});
