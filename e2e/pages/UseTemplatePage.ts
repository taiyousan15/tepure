import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Use Template Page
 */
export class UseTemplatePage {
  readonly page: Page;
  readonly heading: Locator;
  readonly form: Locator;
  readonly submitButton: Locator;
  readonly successMessage: Locator;
  readonly errorMessage: Locator;
  readonly backButton: Locator;
  readonly loadingIndicator: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator('h1, h2').first();
    this.form = page.locator('form');
    this.submitButton = page.locator('button[type="submit"], button:has-text("送信"), button:has-text("Submit")');
    this.successMessage = page.locator('[role="alert"].success, .success-message');
    this.errorMessage = page.locator('[role="alert"].error, .error-message');
    this.backButton = page.locator('button:has-text("戻る"), button:has-text("Back"), a:has-text("戻る")');
    this.loadingIndicator = page.locator('[role="status"], .loading, .spinner');
  }

  /**
   * Navigate to use template page
   */
  async goto(templateId: string): Promise<void> {
    await this.page.goto(`/templates/${templateId}/use`);
  }

  /**
   * Fill form input by label
   */
  async fillInputByLabel(label: string, value: string): Promise<void> {
    const input = this.page.locator(`input[aria-label="${label}"], input[placeholder*="${label}"]`).first();
    await input.fill(value);
  }

  /**
   * Fill form input by name
   */
  async fillInputByName(name: string, value: string): Promise<void> {
    const input = this.form.locator(`input[name="${name}"], textarea[name="${name}"]`);
    await input.fill(value);
  }

  /**
   * Fill all form inputs
   */
  async fillForm(data: Record<string, string>): Promise<void> {
    for (const [key, value] of Object.entries(data)) {
      await this.fillInputByName(key, value);
    }
  }

  /**
   * Submit form
   */
  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Fill and submit form
   */
  async fillAndSubmit(data: Record<string, string>): Promise<void> {
    await this.fillForm(data);
    await this.submit();
  }

  /**
   * Wait for success message
   */
  async waitForSuccess(): Promise<void> {
    await this.successMessage.waitFor({ state: 'visible', timeout: 10000 });
  }

  /**
   * Wait for error message
   */
  async waitForError(): Promise<void> {
    await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 });
  }

  /**
   * Click back button
   */
  async goBack(): Promise<void> {
    await this.backButton.click();
  }

  /**
   * Check if form is valid
   */
  async isFormValid(): Promise<boolean> {
    return this.submitButton.isEnabled();
  }

  /**
   * Check if on use template page
   */
  async isOnUseTemplatePage(): Promise<boolean> {
    return this.page.url().includes('/use');
  }

  /**
   * Get success message text
   */
  async getSuccessMessage(): Promise<string | null> {
    return this.successMessage.textContent();
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoadingComplete(): Promise<void> {
    await this.loadingIndicator.waitFor({ state: 'hidden', timeout: 30000 });
  }
}
