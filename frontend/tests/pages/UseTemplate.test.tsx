/**
 * UseTemplate component tests
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import UseTemplate from '../../src/pages/UseTemplate';
import {
  renderWithRouter,
  mockFetchResponse,
  mockFetchError,
  setAuthToken,
  clearLocalStorage,
  createMockTemplateDetail,
  createMockField,
  userEvent,
} from '../utils';

// Mock useParams and useNavigate
const mockNavigate = vi.fn();
const mockParams = { templateId: 'template-1' };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => mockParams,
    useNavigate: () => mockNavigate,
  };
});

// Mock window.alert
const mockAlert = vi.fn();

describe('UseTemplate Component', () => {
  beforeEach(() => {
    clearLocalStorage();
    setAuthToken('test-token');
    mockNavigate.mockClear();
    mockAlert.mockClear();
    window.alert = mockAlert;
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render loading state initially', () => {
      renderWithRouter(<UseTemplate />);
      expect(screen.getByText('読み込み中...')).toBeInTheDocument();
    });

    it('should render page title and back button', async () => {
      const template = createMockTemplateDetail({
        id: 'template-1',
        name: 'Test Template',
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('テンプレートを使用')).toBeInTheDocument();
        expect(screen.getByText('テンプレート: Test Template')).toBeInTheDocument();
        expect(screen.getByText('← テンプレート一覧に戻る')).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('should fetch template detail on mount', async () => {
      const fetchSpy = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => createMockTemplateDetail(),
      } as Response);

      global.fetch = fetchSpy;

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(fetchSpy).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/templates/template-1'),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token',
            }),
          })
        );
      });
    });

    it('should display error when template fetch fails', async () => {
      mockFetchError('テンプレート情報の取得に失敗しました');

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText(/テンプレート情報の取得に失敗しました/i)).toBeInTheDocument();
      });
    });

    it('should display error when template not found', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({}),
      } as Response);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText(/テンプレート情報の取得に失敗しました/i)).toBeInTheDocument();
      });
    });
  });

  describe('Template Preview', () => {
    it('should display template preview image', async () => {
      const template = createMockTemplateDetail({
        name: 'Test Template',
        preview_url: 'https://example.com/preview.png',
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        const previewImage = screen.getByAltText('Test Template');
        expect(previewImage).toBeInTheDocument();
        expect(previewImage).toHaveAttribute('src', 'https://example.com/preview.png');
      });
    });

    it('should display placeholder when no preview image', async () => {
      const template = createMockTemplateDetail({
        preview_url: '',
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('プレビュー画像なし')).toBeInTheDocument();
      });
    });

    it('should display usage instructions', async () => {
      const template = createMockTemplateDetail();

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('📌 使い方')).toBeInTheDocument();
        expect(screen.getByText('右側のフォームに内容を入力')).toBeInTheDocument();
        expect(screen.getByText('「テンプレートを生成」をクリック')).toBeInTheDocument();
        expect(screen.getByText('Figmaプラグインで確認・書き出し')).toBeInTheDocument();
      });
    });
  });

  describe('Form Fields', () => {
    it('should display all template fields', async () => {
      const template = createMockTemplateDetail({
        fields: [
          createMockField({
            id: 'field-1',
            node_id: 'node-1',
            layer_name: 'Title',
            default_value: 'Default Title',
            required: true,
          }),
          createMockField({
            id: 'field-2',
            node_id: 'node-2',
            layer_name: 'Description',
            default_value: 'Default Description',
            required: false,
          }),
        ],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('入力フィールド (2個)')).toBeInTheDocument();
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
        expect(screen.getByLabelText(/Description/)).toBeInTheDocument();
      });
    });

    it('should mark required fields with asterisk', async () => {
      const template = createMockTemplateDetail({
        fields: [
          createMockField({
            layer_name: 'Required Field',
            required: true,
          }),
          createMockField({
            layer_name: 'Optional Field',
            required: false,
          }),
        ],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        const requiredLabel = screen.getByText('Required Field').closest('label');
        expect(requiredLabel?.textContent).toContain('*');
      });
    });

    it('should populate fields with default values', async () => {
      const template = createMockTemplateDetail({
        fields: [
          createMockField({
            node_id: 'node-1',
            layer_name: 'Title',
            default_value: 'Default Title',
          }),
        ],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        const input = screen.getByLabelText(/Title/) as HTMLInputElement;
        expect(input.value).toBe('Default Title');
      });
    });

    it('should display node ID for each field', async () => {
      const template = createMockTemplateDetail({
        fields: [
          createMockField({
            node_id: 'node-abc-123',
            layer_name: 'Title',
          }),
        ],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('node-abc-123')).toBeInTheDocument();
      });
    });

    it('should display empty state when no fields', async () => {
      const template = createMockTemplateDetail({
        fields: [],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('フィールド情報がありません')).toBeInTheDocument();
      });
    });
  });

  describe('Form Interaction', () => {
    it('should update field values on input change', async () => {
      const user = userEvent.setup();
      const template = createMockTemplateDetail({
        fields: [
          createMockField({
            node_id: 'node-1',
            layer_name: 'Title',
            default_value: '',
          }),
        ],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      const input = screen.getByLabelText(/Title/) as HTMLInputElement;
      await user.clear(input);
      await user.type(input, 'New Title');

      expect(input.value).toBe('New Title');
    });

    it('should disable submit button when no fields', async () => {
      const template = createMockTemplateDetail({
        fields: [],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        const submitButton = screen.getByText('✨ テンプレートを生成');
        expect(submitButton).toBeDisabled();
      });
    });

    it('should enable submit button when fields exist', async () => {
      const template = createMockTemplateDetail({
        fields: [createMockField()],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        const submitButton = screen.getByText('✨ テンプレートを生成');
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form with field values', async () => {
      const user = userEvent.setup();
      const fetchSpy = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates/')) {
          return Promise.resolve({
            ok: true,
            json: async () =>
              createMockTemplateDetail({
                fields: [
                  createMockField({
                    node_id: 'node-1',
                    layer_name: 'Title',
                    default_value: 'Default',
                  }),
                ],
              }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              job_id: 'job-123',
              template_name: 'Test Template',
              message: 'Job created successfully',
            }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      global.fetch = fetchSpy;

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Title/)).toBeInTheDocument();
      });

      const input = screen.getByLabelText(/Title/);
      await user.clear(input);
      await user.type(input, 'My Title');

      const submitButton = screen.getByText('✨ テンプレートを生成');
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetchSpy).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/jobs'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('My Title'),
          })
        );
      });
    });

    it('should display success alert and navigate on successful submission', async () => {
      const user = userEvent.setup();

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates/')) {
          return Promise.resolve({
            ok: true,
            json: async () =>
              createMockTemplateDetail({
                fields: [createMockField()],
              }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              job_id: 'job-123',
              template_name: 'Test Template',
              message: 'Job created successfully',
            }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('✨ テンプレートを生成')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('✨ テンプレートを生成');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          expect.stringContaining('ジョブ作成成功')
        );
        expect(mockNavigate).toHaveBeenCalledWith('/templates');
      });
    });

    it('should display submitting state during submission', async () => {
      const user = userEvent.setup();

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates/')) {
          return Promise.resolve({
            ok: true,
            json: async () =>
              createMockTemplateDetail({
                fields: [createMockField()],
              }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => ({
                  job_id: 'job-123',
                  template_name: 'Test Template',
                  message: 'Job created',
                }),
              } as Response);
            }, 100);
          });
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('✨ テンプレートを生成')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('✨ テンプレートを生成');
      await user.click(submitButton);

      expect(screen.getByText('生成中...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText('生成中...')).not.toBeInTheDocument();
      });
    });

    it('should display error message when submission fails', async () => {
      const user = userEvent.setup();

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates/')) {
          return Promise.resolve({
            ok: true,
            json: async () =>
              createMockTemplateDetail({
                fields: [createMockField()],
              }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: false,
            status: 400,
            json: async () => ({
              error: { message: 'Invalid input data' },
            }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('✨ テンプレートを生成')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('✨ テンプレートを生成');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Invalid input data/i)).toBeInTheDocument();
      });
    });

    it('should handle network errors during submission', async () => {
      const user = userEvent.setup();

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates/')) {
          return Promise.resolve({
            ok: true,
            json: async () =>
              createMockTemplateDetail({
                fields: [createMockField()],
              }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('✨ テンプレートを生成')).toBeInTheDocument();
      });

      const submitButton = screen.getByText('✨ テンプレートを生成');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate back to templates when clicking back button', async () => {
      const user = userEvent.setup();
      const template = createMockTemplateDetail();

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('← テンプレート一覧に戻る')).toBeInTheDocument();
      });

      const backButton = screen.getByText('← テンプレート一覧に戻る');
      await user.click(backButton);

      expect(mockNavigate).toHaveBeenCalledWith('/templates');
    });

    it('should show back button on error state', async () => {
      mockFetchError('Error occurred');

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('← テンプレート一覧に戻る')).toBeInTheDocument();
      });
    });
  });

  describe('Required Field Validation', () => {
    it('should validate required fields on submit', async () => {
      const user = userEvent.setup();
      const template = createMockTemplateDetail({
        fields: [
          createMockField({
            node_id: 'node-1',
            layer_name: 'Required Field',
            required: true,
            default_value: '',
          }),
        ],
      });

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByLabelText(/Required Field/)).toBeInTheDocument();
      });

      const input = screen.getByLabelText(/Required Field/) as HTMLInputElement;
      expect(input.required).toBe(true);

      // Clear the input
      await user.clear(input);

      const submitButton = screen.getByText('✨ テンプレートを生成');
      await user.click(submitButton);

      // HTML5 validation should prevent submission
      // The form should not call the API
      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/jobs'),
        expect.any(Object)
      );
    });
  });

  describe('Authentication', () => {
    it('should include auth token in API requests', async () => {
      const fetchSpy = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => createMockTemplateDetail(),
      } as Response);

      global.fetch = fetchSpy;

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(fetchSpy).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            headers: expect.objectContaining({
              Authorization: 'Bearer test-token',
            }),
          })
        );
      });
    });
  });

  describe('Layout', () => {
    it('should use two-column layout', async () => {
      const template = createMockTemplateDetail();

      mockFetchResponse(template);

      renderWithRouter(<UseTemplate />);

      await waitFor(() => {
        expect(screen.getByText('プレビュー')).toBeInTheDocument();
        expect(screen.getByText(/入力フィールド/)).toBeInTheDocument();
      });
    });
  });
});
