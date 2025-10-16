import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Dashboard Page
 */
export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly logoutButton: Locator;
  readonly templatesLink: Locator;
  readonly userEmail: Locator;
  readonly navigation: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator('h1, h2').first();
    this.logoutButton = page.locator('button:has-text("ログアウト"), button:has-text("Logout")');
    this.templatesLink = page.locator('a:has-text("テンプレート"), a[href="/templates"]');
    this.userEmail = page.locator('nav .text-sm').first();
    this.navigation = page.locator('nav');
  }

  /**
   * Navigate to dashboard
   */
  async goto(): Promise<void> {
    await this.page.goto('/');
  }

  /**
   * Click logout button
   */
  async logout(): Promise<void> {
    await this.logoutButton.click();
  }

  /**
   * Navigate to templates page
   */
  async goToTemplates(): Promise<void> {
    await this.templatesLink.click();
  }

  /**
   * Check if navigation is visible
   */
  async isNavigationVisible(): Promise<boolean> {
    return this.navigation.isVisible();
  }

  /**
   * Get logged in user email
   */
  async getUserEmail(): Promise<string | null> {
    return this.userEmail.textContent();
  }

  /**
   * Check if on dashboard page
   */
  async isOnDashboardPage(): Promise<boolean> {
    return this.page.url().endsWith('/') || this.page.url().includes('/dashboard');
  }
}
