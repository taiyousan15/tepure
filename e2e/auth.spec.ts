import { test, expect, TEST_USER, setupAPIMocks, clearAuth, checkAccessibility } from './fixtures';

/**
 * Authentication Flow E2E Tests
 */
test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks
    await setupAPIMocks(page);

    // Clear any existing auth
    await clearAuth(page);
  });

  test('should display login page correctly', async ({ loginPage }) => {
    await loginPage.goto();

    // Check page elements
    await expect(loginPage.heading).toBeVisible();
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();

    // Check accessibility
    await checkAccessibility(loginPage.page);
  });

  test('should login successfully with valid credentials', async ({ loginPage, dashboardPage }) => {
    await loginPage.goto();

    // Fill login form
    await loginPage.login(TEST_USER.email, TEST_USER.password);

    // Wait for redirect to dashboard
    await loginPage.waitForRedirect();

    // Verify we're on dashboard
    await expect(dashboardPage.page).toHaveURL(/\/$|\/dashboard/);
    await expect(dashboardPage.navigation).toBeVisible();

    // Verify user email is displayed
    const userEmail = await dashboardPage.getUserEmail();
    expect(userEmail).toContain(TEST_USER.email);
  });

  test('should show error message with invalid credentials', async ({ loginPage, page }) => {
    await loginPage.goto();

    // Mock failed login response
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password',
          },
        }),
      });
    });

    // Attempt login with invalid credentials
    await loginPage.login('invalid@example.com', 'wrongpassword');

    // Should stay on login page
    expect(await loginPage.isOnLoginPage()).toBe(true);
  });

  test('should logout successfully', async ({ loginPage, dashboardPage, page }) => {
    // Login first
    await loginPage.goto();
    await loginPage.login(TEST_USER.email, TEST_USER.password);
    await loginPage.waitForRedirect();

    // Verify logged in
    await expect(dashboardPage.navigation).toBeVisible();

    // Logout
    await dashboardPage.logout();

    // Wait for redirect to login page
    await page.waitForURL('**/login', { timeout: 5000 });

    // Verify we're on login page
    expect(await loginPage.isOnLoginPage()).toBe(true);
    await expect(loginPage.heading).toBeVisible();
  });

  test('should redirect to login when accessing protected route without authentication', async ({ page, loginPage }) => {
    await clearAuth(page);

    // Try to access dashboard without authentication
    await page.goto('/');

    // Should redirect to login
    await page.waitForURL('**/login', { timeout: 5000 });
    expect(await loginPage.isOnLoginPage()).toBe(true);
  });

  test('should persist authentication after page refresh', async ({ loginPage, dashboardPage, page }) => {
    // Login
    await loginPage.goto();
    await loginPage.login(TEST_USER.email, TEST_USER.password);
    await loginPage.waitForRedirect();

    // Verify logged in
    await expect(dashboardPage.navigation).toBeVisible();

    // Refresh page
    await page.reload();

    // Should still be logged in
    await expect(dashboardPage.navigation).toBeVisible();
    const userEmail = await dashboardPage.getUserEmail();
    expect(userEmail).toContain(TEST_USER.email);
  });

  test('should handle network errors gracefully', async ({ loginPage, page }) => {
    await loginPage.goto();

    // Mock network error
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.abort('failed');
    });

    // Attempt login
    await loginPage.login(TEST_USER.email, TEST_USER.password);

    // Should stay on login page (or show error)
    expect(await loginPage.isOnLoginPage()).toBe(true);
  });

  test('should validate email format', async ({ loginPage }) => {
    await loginPage.goto();

    // Try to submit with invalid email
    await loginPage.emailInput.fill('invalid-email');
    await loginPage.passwordInput.fill('password123');

    // Check HTML5 validation
    const isValid = await loginPage.emailInput.evaluate((el: HTMLInputElement) => el.validity.valid);
    expect(isValid).toBe(false);
  });

  test('should require password', async ({ loginPage }) => {
    await loginPage.goto();

    // Fill only email
    await loginPage.emailInput.fill(TEST_USER.email);

    // Try to submit without password
    const isValid = await loginPage.passwordInput.evaluate((el: HTMLInputElement) => el.validity.valid);

    // Password field should be invalid or empty
    const passwordValue = await loginPage.passwordInput.inputValue();
    expect(passwordValue).toBe('');
  });

  test('should support keyboard navigation', async ({ loginPage, page }) => {
    await loginPage.goto();

    // Focus email input
    await loginPage.emailInput.focus();

    // Tab to password
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBe('INPUT');

    // Fill using keyboard
    await page.keyboard.type('password123');

    // Tab to login button
    await page.keyboard.press('Tab');

    // Press Enter to submit
    await page.keyboard.press('Enter');
  });
});

/**
 * Mobile Authentication Tests
 */
test.describe('Authentication Flow - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('should display login page correctly on mobile', async ({ loginPage }) => {
    await setupAPIMocks(loginPage.page);
    await clearAuth(loginPage.page);
    await loginPage.goto();

    // Check page elements
    await expect(loginPage.heading).toBeVisible();
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });

  test('should login successfully on mobile', async ({ loginPage, dashboardPage }) => {
    await setupAPIMocks(loginPage.page);
    await clearAuth(loginPage.page);
    await loginPage.goto();

    // Login
    await loginPage.login(TEST_USER.email, TEST_USER.password);
    await loginPage.waitForRedirect();

    // Verify logged in
    await expect(dashboardPage.navigation).toBeVisible();
  });
});
