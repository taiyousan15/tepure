/**
 * Test utilities for React Testing Library
 */
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

/**
 * Custom render function that includes Router
 */
export function renderWithRouter(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <BrowserRouter>{children}</BrowserRouter>;
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Mock fetch response helper
 */
export function mockFetchResponse<T>(data: T, status = 200): void {
  global.fetch = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers(),
    redirected: false,
    statusText: status === 200 ? 'OK' : 'Error',
    type: 'basic' as ResponseType,
    url: '',
    clone: vi.fn(),
    body: null,
    bodyUsed: false,
    arrayBuffer: async () => new ArrayBuffer(0),
    blob: async () => new Blob(),
    formData: async () => new FormData(),
  } as Response);
}

/**
 * Mock fetch error helper
 */
export function mockFetchError(message = 'Fetch error'): void {
  global.fetch = vi.fn().mockRejectedValue(new Error(message));
}

/**
 * Mock fetch with custom handler
 */
export function mockFetchWithHandler(
  handler: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
): void {
  global.fetch = vi.fn().mockImplementation(handler);
}

/**
 * Wait for async updates
 */
export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Mock localStorage with initial data
 */
export function mockLocalStorage(data: Record<string, string> = {}): void {
  Object.keys(data).forEach((key) => {
    window.localStorage.setItem(key, data[key]);
  });
}

/**
 * Clear localStorage
 */
export function clearLocalStorage(): void {
  window.localStorage.clear();
}

/**
 * Set auth token in localStorage
 */
export function setAuthToken(token = 'test-token'): void {
  window.localStorage.setItem('auth_token', token);
}

/**
 * Remove auth token from localStorage
 */
export function removeAuthToken(): void {
  window.localStorage.removeItem('auth_token');
}

/**
 * Create mock template data
 */
export function createMockTemplate(overrides = {}) {
  return {
    id: 'template-1',
    name: 'Test Template',
    category: 'LP',
    preview_url: 'https://example.com/preview.png',
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock job data
 */
export function createMockJob(overrides = {}) {
  return {
    job_id: 'job-1',
    template_id: 'template-1',
    status: 'completed',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    ...overrides,
  };
}

/**
 * Create mock field data
 */
export function createMockField(overrides = {}) {
  return {
    id: 'field-1',
    node_id: 'node-1',
    type: 'TEXT',
    layer_name: 'Test Layer',
    default_value: 'Default Value',
    required: false,
    ...overrides,
  };
}

/**
 * Create mock template detail with fields
 */
export function createMockTemplateDetail(overrides = {}) {
  return {
    id: 'template-1',
    name: 'Test Template',
    category: 'LP',
    preview_url: 'https://example.com/preview.png',
    figma_file_key: 'test-file-key',
    figma_node_id: 'test-node-id',
    fields: [createMockField()],
    ...overrides,
  };
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
