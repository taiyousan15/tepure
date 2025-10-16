# E2E Testing Documentation

## Overview

This directory contains End-to-End (E2E) tests for the Figma Template Automation application using Playwright.

## Test Structure

```
e2e/
├── pages/                      # Page Object Models
│   ├── LoginPage.ts           # Login page interactions
│   ├── DashboardPage.ts       # Dashboard page interactions
│   ├── TemplatesPage.ts       # Templates list page interactions
│   ├── UseTemplatePage.ts     # Use template page interactions
│   └── CreateTemplatePage.ts  # Create template page interactions
├── fixtures.ts                 # Test fixtures and helpers
├── auth.spec.ts               # Authentication flow tests
├── templates.spec.ts          # Template browsing tests
├── use-template.spec.ts       # Template usage tests
├── create-template.spec.ts    # Template registration tests
└── README.md                  # This file
```

## Prerequisites

- Node.js 18+ installed
- Frontend development server running on `http://localhost:5173`
- Backend API available (or mocked)

## Installation

Install Playwright and dependencies:

```bash
npm install @playwright/test --save-dev
npx playwright install
```

## Running Tests

### Run all tests

```bash
npx playwright test
```

### Run specific test file

```bash
npx playwright test e2e/auth.spec.ts
```

### Run tests in headed mode (with browser UI)

```bash
npx playwright test --headed
```

### Run tests in debug mode

```bash
npx playwright test --debug
```

### Run tests in specific browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run tests on mobile viewport

```bash
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"
```

### Run tests with UI mode

```bash
npx playwright test --ui
```

## Test Reports

### View HTML report

```bash
npx playwright show-report
```

### Generate coverage report

Coverage is tracked via screenshots and videos on failure.

## Test Organization

### Page Object Model (POM)

All page interactions are encapsulated in Page Object classes located in `e2e/pages/`. This provides:

- **Reusability**: Common actions are defined once
- **Maintainability**: UI changes only require updates in one place
- **Readability**: Tests are more readable and declarative

Example:

```typescript
// Using Page Object
await loginPage.login('user@example.com', 'password');

// Instead of:
await page.locator('input[type="email"]').fill('user@example.com');
await page.locator('input[type="password"]').fill('password');
await page.locator('button:has-text("Login")').click();
```

### Fixtures

Custom fixtures are defined in `fixtures.ts`:

- **Test fixtures**: Page objects, authentication helpers
- **Mock responses**: Predefined API responses for testing
- **Helper functions**: Setup, teardown, and utility functions

Example:

```typescript
test('should login successfully', async ({ loginPage, dashboardPage }) => {
  await loginPage.goto();
  await loginPage.login(TEST_USER.email, TEST_USER.password);
  await expect(dashboardPage.navigation).toBeVisible();
});
```

## Test Scenarios

### 1. Authentication Flow (`auth.spec.ts`)

Tests user authentication functionality:

- Display login page
- Login with valid credentials
- Show error with invalid credentials
- Logout successfully
- Redirect to login for protected routes
- Persist authentication after refresh
- Handle network errors
- Form validation
- Keyboard navigation
- Mobile authentication

**Key Features:**
- OAuth mock integration
- Session persistence testing
- Error handling validation

### 2. Template Browsing (`templates.spec.ts`)

Tests template listing and browsing:

- Display templates list
- Load templates from API
- Search templates by name
- Filter by category
- Open template detail modal
- Close modal
- Navigate to use template page
- Navigate to create template page
- Handle empty results
- Handle API errors
- Keyboard navigation
- Display thumbnails
- Display metadata
- Mobile browsing
- Accessibility

**Key Features:**
- Search and filter functionality
- Modal interactions
- Responsive design testing

### 3. Template Usage (`use-template.spec.ts`)

Tests the complete template usage workflow:

- Display use template page
- Display template information
- Fill and submit form
- Validate required fields
- Handle API errors
- Navigate back
- Show loading state
- Poll job status
- Display generated Figma URL
- Handle form validation
- Preserve form data on error
- Keyboard shortcuts
- Mobile usage
- Network timeout handling
- Job failure handling

**Key Features:**
- Form validation
- Async job processing
- Error recovery
- Loading states

### 4. Template Registration (`create-template.spec.ts`)

Tests template creation functionality:

- Display create template page
- Create template successfully
- Validate required fields
- Validate Figma URL format
- Handle API errors
- Cancel form
- Upload thumbnail
- Validate field lengths
- Show category options
- Preserve form data on error
- Disable submit during submission
- Keyboard navigation
- Validate duplicate names
- Mobile registration
- Accessibility
- Form validation

**Key Features:**
- File upload testing
- Duplicate detection
- Multi-field validation

## API Mocking

All tests use API mocks defined in `fixtures.ts`. This provides:

- **Isolation**: Tests don't depend on backend availability
- **Speed**: No network latency
- **Reliability**: Consistent test results
- **Control**: Test error scenarios easily

### Mock Setup

```typescript
await setupAPIMocks(page);
```

This mocks all API endpoints including:
- `/api/v1/auth/login` - Authentication
- `/api/v1/templates` - Template CRUD operations
- `/api/v1/templates/:id/use` - Template usage
- `/api/v1/jobs/:id` - Job status polling

### Custom Mocks

Override specific endpoints in individual tests:

```typescript
await page.route('**/api/v1/templates', async (route) => {
  await route.fulfill({
    status: 500,
    contentType: 'application/json',
    body: JSON.stringify({ error: { message: 'Server Error' } }),
  });
});
```

## Authentication Helper

Use `setupAuthenticatedSession()` to pre-authenticate tests:

```typescript
test.beforeEach(async ({ page }) => {
  await setupAuthenticatedSession(page);
  await setupAPIMocks(page);
});
```

This sets mock tokens in localStorage to bypass login.

## Accessibility Testing

Tests include basic accessibility checks:

- Semantic HTML structure
- ARIA labels and roles
- Keyboard navigation
- Screen reader support
- Focus management

Use the `checkAccessibility()` helper:

```typescript
await checkAccessibility(page);
```

## Browser Support

Tests run on multiple browsers:

- **Chromium** (Chrome, Edge)
- **Firefox**
- **WebKit** (Safari)
- **Mobile Chrome** (Pixel 5 viewport)
- **Mobile Safari** (iPhone 12 viewport)

## CI/CD Integration

Tests are configured to run in CI environments:

- Retry failed tests 2 times
- Run tests sequentially in CI
- Generate HTML and JSON reports
- Capture screenshots and videos on failure

### GitHub Actions Example

```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E tests
  run: npx playwright test
  env:
    CI: true

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Debugging

### Visual debugging

```bash
npx playwright test --debug
```

### Generate trace

```bash
npx playwright test --trace on
```

View trace:

```bash
npx playwright show-trace trace.zip
```

### Screenshots and videos

Failed tests automatically capture:
- Screenshots (saved to `test-results/`)
- Videos (saved to `test-results/`)

## Best Practices

### 1. Use Page Object Model

Encapsulate page interactions in POM classes.

### 2. Use data-testid attributes

For stable selectors:

```html
<div data-testid="template-card">...</div>
```

```typescript
page.locator('[data-testid="template-card"]')
```

### 3. Wait for network idle

```typescript
await page.waitForLoadState('networkidle');
```

### 4. Use specific locators

Prefer specific locators over generic ones:

```typescript
// Good
page.locator('[data-testid="login-button"]')
page.locator('button[type="submit"]')

// Avoid
page.locator('button').first()
page.locator('.btn')
```

### 5. Independent tests

Each test should be independent and not rely on other tests.

### 6. Clean up after tests

Use `beforeEach` and `afterEach` hooks:

```typescript
test.beforeEach(async ({ page }) => {
  await clearAuth(page);
  await setupAPIMocks(page);
});
```

### 7. Test error scenarios

Don't just test happy paths - test error handling too.

### 8. Use fixtures

Leverage custom fixtures for common setup:

```typescript
test('my test', async ({ loginPage, dashboardPage }) => {
  // Pages are automatically initialized
});
```

## Performance Considerations

- Tests run in parallel by default (set `workers` in config)
- Use `test.describe.serial()` for sequential tests within a suite
- Mock network requests to avoid latency
- Use `test.slow()` for known slow tests

## Troubleshooting

### Tests timing out

Increase timeout in `playwright.config.ts`:

```typescript
use: {
  actionTimeout: 30000, // 30 seconds
}
```

### Flaky tests

- Use `waitFor` instead of `waitForTimeout`
- Increase retries in CI
- Check for race conditions
- Use stricter locators

### Browser not found

```bash
npx playwright install
```

### Port already in use

Ensure no other process is using port 5173:

```bash
lsof -ti:5173 | xargs kill -9
```

## Coverage

E2E tests cover:

- **Authentication**: Login, logout, session management
- **Template browsing**: List, search, filter, view details
- **Template usage**: Form submission, job processing, results
- **Template creation**: Form validation, submission, error handling
- **Error handling**: Network errors, API errors, validation errors
- **Mobile responsive**: All flows on mobile viewports
- **Accessibility**: Basic ARIA, keyboard navigation, screen readers

## Maintenance

### Updating tests

When UI changes:

1. Update Page Object Models in `e2e/pages/`
2. Update locators as needed
3. Re-run tests to verify

### Adding new tests

1. Create test file in `e2e/` directory
2. Use existing fixtures and page objects
3. Follow naming convention: `*.spec.ts`
4. Add test documentation here

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Debugging Guide](https://playwright.dev/docs/debug)

## License

MIT
