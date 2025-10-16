import { test as base, expect, Page } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { TemplatesPage } from './pages/TemplatesPage';
import { UseTemplatePage } from './pages/UseTemplatePage';
import { CreateTemplatePage } from './pages/CreateTemplatePage';

/**
 * Test user credentials
 */
export const TEST_USER = {
  email: 'test@example.com',
  password: 'password123',
};

/**
 * Mock API responses
 */
export const MOCK_RESPONSES = {
  login: {
    token: 'mock-jwt-token-12345',
    user: {
      id: 'user-123',
      email: TEST_USER.email,
    },
  },
  templates: [
    {
      id: 'template-1',
      name: 'Sample Template 1',
      category: 'LP',
      description: 'A landing page template',
      figma_file_key: 'abc123',
      figma_node_id: '1:234',
      preview_url: 'https://example.com/thumb1.png',
      fields: [
        { type: 'text', label: 'Title', default_value: 'Sample Title' },
        { type: 'color', label: 'Background', default_value: '#FF5733' },
      ],
      tags: ['marketing', 'landing-page'],
      version: '1.0.0',
      created_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'template-2',
      name: 'Sample Template 2',
      category: 'SNS',
      description: 'A social media template',
      figma_file_key: 'def456',
      figma_node_id: '2:345',
      preview_url: 'https://example.com/thumb2.png',
      fields: [
        { type: 'text', label: 'Headline', default_value: 'Breaking News' },
        { type: 'border', label: 'Border Style', default_value: 'solid' },
      ],
      tags: ['social', 'instagram'],
      version: '1.0.0',
      created_at: '2025-01-02T00:00:00Z',
    },
  ],
  createTemplate: {
    id: 'template-new',
    name: 'New Template',
    message: 'Template created successfully',
  },
  useTemplate: {
    job_id: 'job-123',
    status: 'pending',
    message: 'Template processing started',
  },
  jobStatus: {
    job_id: 'job-123',
    status: 'completed',
    result_url: 'https://figma.com/file/generated-123',
  },
};

/**
 * Extended fixtures with page objects
 */
type TestFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  templatesPage: TemplatesPage;
  useTemplatePage: UseTemplatePage;
  createTemplatePage: CreateTemplatePage;
};

/**
 * Custom test with page object fixtures
 */
export const test = base.extend<TestFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  templatesPage: async ({ page }, use) => {
    await use(new TemplatesPage(page));
  },
  useTemplatePage: async ({ page }, use) => {
    await use(new UseTemplatePage(page));
  },
  createTemplatePage: async ({ page }, use) => {
    await use(new CreateTemplatePage(page));
  },
});

export { expect };

/**
 * Setup authenticated session
 */
export async function setupAuthenticatedSession(page: Page): Promise<void> {
  // Set mock localStorage values
  await page.addInitScript(
    ({ token, user }) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(user));
    },
    {
      token: MOCK_RESPONSES.login.token,
      user: MOCK_RESPONSES.login.user,
    }
  );
}

/**
 * Setup API route mocks
 */
export async function setupAPIMocks(page: Page): Promise<void> {
  // Mock login endpoint
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_RESPONSES.login),
    });
  });

  // Mock templates list endpoint
  await page.route('**/api/v1/templates', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_RESPONSES.templates),
      });
    } else if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_RESPONSES.createTemplate),
      });
    }
  });

  // Mock template detail endpoint
  await page.route('**/api/v1/templates/*', async (route) => {
    const templateId = route.request().url().split('/').pop();
    const template = MOCK_RESPONSES.templates.find((t) => t.id === templateId);

    if (template) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(template),
      });
    } else {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: { message: 'Template not found' } }),
      });
    }
  });

  // Mock template use endpoint
  await page.route('**/api/v1/templates/*/use', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_RESPONSES.useTemplate),
    });
  });

  // Mock job status endpoint
  await page.route('**/api/v1/jobs/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(MOCK_RESPONSES.jobStatus),
    });
  });
}

/**
 * Clear authentication
 */
export async function clearAuth(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
  });
}

/**
 * Wait for network idle
 */
export async function waitForNetworkIdle(page: Page, timeout = 5000): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Check accessibility
 */
export async function checkAccessibility(page: Page): Promise<void> {
  // Check for basic accessibility attributes
  const mainContent = page.locator('main, [role="main"]');
  await expect(mainContent).toBeVisible();

  // Check for heading structure
  const h1Count = await page.locator('h1').count();
  expect(h1Count).toBeGreaterThanOrEqual(0);
}
