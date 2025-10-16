import { Page, Locator } from '@playwright/test';

/**
 * Page Object Model for Create Template Page
 */
export class CreateTemplatePage {
  readonly page: Page;
  readonly heading: Locator;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly categorySelect: Locator;
  readonly figmaUrlInput: Locator;
  readonly thumbnailInput: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;
  readonly successMessage: Locator;
  readonly errorMessage: Locator;
  readonly form: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator('h1, h2').first();
    this.form = page.locator('form');
    this.nameInput = page.locator('input[name="name"], input[placeholder*="名前"], input[placeholder*="name"]');
    this.descriptionInput = page.locator('textarea[name="description"], textarea[placeholder*="説明"]');
    this.categorySelect = page.locator('select[name="category"], input[name="category"]');
    this.figmaUrlInput = page.locator('input[name="figma_url"], input[placeholder*="Figma"]');
    this.thumbnailInput = page.locator('input[type="file"], input[name="thumbnail"]');
    this.submitButton = page.locator('button[type="submit"], button:has-text("作成"), button:has-text("Create")');
    this.cancelButton = page.locator('button:has-text("キャンセル"), button:has-text("Cancel"), a:has-text("戻る")');
    this.successMessage = page.locator('[role="alert"].success, .success-message');
    this.errorMessage = page.locator('[role="alert"].error, .error-message');
  }

  /**
   * Navigate to create template page
   */
  async goto(): Promise<void> {
    await this.page.goto('/templates/create');
  }

  /**
   * Fill template name
   */
  async fillName(name: string): Promise<void> {
    await this.nameInput.fill(name);
  }

  /**
   * Fill template description
   */
  async fillDescription(description: string): Promise<void> {
    await this.descriptionInput.fill(description);
  }

  /**
   * Select category
   */
  async selectCategory(category: string): Promise<void> {
    await this.categorySelect.selectOption(category);
  }

  /**
   * Fill Figma URL
   */
  async fillFigmaUrl(url: string): Promise<void> {
    await this.figmaUrlInput.fill(url);
  }

  /**
   * Upload thumbnail
   */
  async uploadThumbnail(filePath: string): Promise<void> {
    await this.thumbnailInput.setInputFiles(filePath);
  }

  /**
   * Fill complete form
   */
  async fillForm(data: {
    name: string;
    description: string;
    category: string;
    figmaUrl: string;
  }): Promise<void> {
    await this.fillName(data.name);
    await this.fillDescription(data.description);
    await this.selectCategory(data.category);
    await this.fillFigmaUrl(data.figmaUrl);
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
  async fillAndSubmit(data: {
    name: string;
    description: string;
    category: string;
    figmaUrl: string;
  }): Promise<void> {
    await this.fillForm(data);
    await this.submit();
  }

  /**
   * Cancel form
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
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
   * Check if form is valid
   */
  async isFormValid(): Promise<boolean> {
    return this.submitButton.isEnabled();
  }

  /**
   * Check if on create template page
   */
  async isOnCreateTemplatePage(): Promise<boolean> {
    return this.page.url().includes('/templates/create');
  }

  /**
   * Wait for redirect after creation
   */
  async waitForRedirect(): Promise<void> {
    await this.page.waitForURL((url) => !url.pathname.includes('/create'), {
      timeout: 5000,
    });
  }
}
