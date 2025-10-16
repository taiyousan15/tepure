import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Templates List Page
 */
export class TemplatesPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly searchInput: Locator;
  readonly categoryFilter: Locator;
  readonly templateCards: Locator;
  readonly createButton: Locator;
  readonly templateModal: Locator;
  readonly modalCloseButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator('h1, h2').first();
    this.searchInput = page.locator('input[type="search"], input[placeholder*="検索"], input[placeholder*="search"]');
    this.categoryFilter = page.locator('select, [role="listbox"]').first();
    this.templateCards = page.locator('[data-testid="template-card"], .template-card');
    this.createButton = page.locator('button:has-text("作成"), button:has-text("Create"), a:has-text("登録")');
    this.templateModal = page.locator('[role="dialog"], .modal');
    this.modalCloseButton = page.locator('[role="dialog"] button:has-text("閉じる"), .modal button:has-text("Close")');
  }

  /**
   * Navigate to templates page
   */
  async goto(): Promise<void> {
    await this.page.goto('/templates');
  }

  /**
   * Search for templates
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  /**
   * Filter by category
   */
  async filterByCategory(category: string): Promise<void> {
    await this.categoryFilter.selectOption(category);
  }

  /**
   * Get template cards count
   */
  async getTemplateCount(): Promise<number> {
    return this.templateCards.count();
  }

  /**
   * Click on template card by index
   */
  async clickTemplate(index: number): Promise<void> {
    await this.templateCards.nth(index).click();
  }

  /**
   * Click on template card by name
   */
  async clickTemplateByName(name: string): Promise<void> {
    await this.page.locator(`[data-testid="template-card"]:has-text("${name}")`).click();
  }

  /**
   * Wait for modal to open
   */
  async waitForModalOpen(): Promise<void> {
    await this.templateModal.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * Close modal
   */
  async closeModal(): Promise<void> {
    await this.modalCloseButton.click();
    await this.templateModal.waitFor({ state: 'hidden', timeout: 5000 });
  }

  /**
   * Click use template button in modal
   */
  async clickUseTemplateInModal(): Promise<void> {
    const useButton = this.templateModal.locator('button:has-text("使用"), button:has-text("Use")');
    await useButton.click();
  }

  /**
   * Navigate to create template page
   */
  async goToCreateTemplate(): Promise<void> {
    await this.createButton.click();
  }

  /**
   * Check if on templates page
   */
  async isOnTemplatesPage(): Promise<boolean> {
    return this.page.url().includes('/templates');
  }

  /**
   * Get template card text by index
   */
  async getTemplateCardText(index: number): Promise<string | null> {
    return this.templateCards.nth(index).textContent();
  }
}
