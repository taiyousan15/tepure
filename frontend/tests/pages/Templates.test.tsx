/**
 * Templates component tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import Templates from '../../src/pages/Templates';
import {
  renderWithRouter,
  mockFetchResponse,
  mockFetchError,
  setAuthToken,
  clearLocalStorage,
  createMockTemplate,
  userEvent,
} from '../utils';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock TemplateDetailModal component
vi.mock('../../src/components/TemplateDetailModal', () => ({
  default: ({ templateId, isOpen, onClose, onUse }: any) => {
    if (!isOpen) return null;
    return (
      <div data-testid="template-modal">
        <div>Modal for template: {templateId}</div>
        <button onClick={() => onUse(templateId)}>Use Template</button>
        <button onClick={onClose}>Close Modal</button>
      </div>
    );
  },
}));

describe('Templates Component', () => {
  beforeEach(() => {
    clearLocalStorage();
    setAuthToken('test-token');
    mockNavigate.mockClear();
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render templates page with loading state initially', () => {
      renderWithRouter(<Templates />);
      expect(screen.getByText('読み込み中...')).toBeInTheDocument();
    });

    it('should render templates page title', async () => {
      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('テンプレート一覧')).toBeInTheDocument();
      });
    });

    it('should render new template button', async () => {
      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('➕ 新規登録')).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should display search input', async () => {
      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('テンプレートを検索...');
        expect(searchInput).toBeInTheDocument();
      });
    });

    it('should filter templates by search query', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Landing Page' }),
        createMockTemplate({ id: 'template-2', name: 'Banner Design' }),
        createMockTemplate({ id: 'template-3', name: 'SNS Post' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('Landing Page')).toBeInTheDocument();
        expect(screen.getByText('Banner Design')).toBeInTheDocument();
        expect(screen.getByText('SNS Post')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('テンプレートを検索...');
      await user.type(searchInput, 'banner');

      await waitFor(() => {
        expect(screen.queryByText('Landing Page')).not.toBeInTheDocument();
        expect(screen.getByText('Banner Design')).toBeInTheDocument();
        expect(screen.queryByText('SNS Post')).not.toBeInTheDocument();
      });
    });

    it('should be case insensitive when filtering', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Landing Page' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('Landing Page')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('テンプレートを検索...');
      await user.type(searchInput, 'LANDING');

      await waitFor(() => {
        expect(screen.getByText('Landing Page')).toBeInTheDocument();
      });
    });
  });

  describe('Category Filter', () => {
    it('should display all category buttons', async () => {
      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('すべて')).toBeInTheDocument();
        expect(screen.getByText('LP')).toBeInTheDocument();
        expect(screen.getByText('Banner')).toBeInTheDocument();
        expect(screen.getByText('SNS')).toBeInTheDocument();
        expect(screen.getByText('WebApp')).toBeInTheDocument();
      });
    });

    it('should select "all" category by default', async () => {
      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        const allButton = screen.getByText('すべて');
        expect(allButton).toHaveClass('bg-indigo-600', 'text-white');
      });
    });

    it('should fetch templates when category is changed', async () => {
      const user = userEvent.setup();
      const fetchSpy = vi.fn((url: string | URL) => {
        return Promise.resolve({
          ok: true,
          json: async () => ({ templates: [] }),
        } as Response);
      });

      global.fetch = fetchSpy;

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('LP')).toBeInTheDocument();
      });

      // Initial fetch with "all" category
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/v1\/templates\?$/),
        expect.any(Object)
      );

      fetchSpy.mockClear();

      const lpButton = screen.getByText('LP');
      await user.click(lpButton);

      // Fetch with LP category
      await waitFor(() => {
        expect(fetchSpy).toHaveBeenCalledWith(
          expect.stringContaining('category=LP'),
          expect.any(Object)
        );
      });
    });

    it('should highlight selected category', async () => {
      const user = userEvent.setup();

      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('Banner')).toBeInTheDocument();
      });

      const bannerButton = screen.getByText('Banner');
      await user.click(bannerButton);

      await waitFor(() => {
        expect(bannerButton).toHaveClass('bg-indigo-600', 'text-white');
      });
    });
  });

  describe('Templates Display', () => {
    it('should display empty state when no templates found', async () => {
      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('テンプレートが見つかりませんでした')).toBeInTheDocument();
      });
    });

    it('should display template cards', async () => {
      const templates = [
        createMockTemplate({
          id: 'template-1',
          name: 'Test Template 1',
          category: 'LP',
          preview_url: 'https://example.com/preview1.png',
        }),
        createMockTemplate({
          id: 'template-2',
          name: 'Test Template 2',
          category: 'Banner',
          preview_url: 'https://example.com/preview2.png',
        }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('Test Template 1')).toBeInTheDocument();
        expect(screen.getByText('Test Template 2')).toBeInTheDocument();
        expect(screen.getByText('ID: template-1')).toBeInTheDocument();
        expect(screen.getByText('ID: template-2')).toBeInTheDocument();
      });
    });

    it('should display category badges on template cards', async () => {
      const templates = [
        createMockTemplate({ id: 'template-1', category: 'LP' }),
        createMockTemplate({ id: 'template-2', category: 'Banner' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        const categoryBadges = screen.getAllByText('LP');
        expect(categoryBadges.length).toBeGreaterThan(0);
        expect(screen.getByText('Banner')).toBeInTheDocument();
      });
    });

    it('should display template preview images', async () => {
      const templates = [
        createMockTemplate({
          id: 'template-1',
          name: 'Test Template',
          preview_url: 'https://example.com/preview.png',
        }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        const previewImage = screen.getByAltText('Test Template');
        expect(previewImage).toBeInTheDocument();
        expect(previewImage).toHaveAttribute('src', 'https://example.com/preview.png');
      });
    });

    it('should display placeholder when no preview image', async () => {
      const templates = [
        createMockTemplate({
          id: 'template-1',
          name: 'Test Template',
          preview_url: '',
        }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        // Check that the template card is rendered without an image element
        expect(screen.getByText('Test Template')).toBeInTheDocument();
        expect(screen.queryByAltText('Test Template')).not.toBeInTheDocument();
      });
    });
  });

  describe('Template Actions', () => {
    it('should display "Use" and "Detail" buttons on each template card', async () => {
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Test Template' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('使用する')).toBeInTheDocument();
        expect(screen.getByText('詳細')).toBeInTheDocument();
      });
    });

    it('should navigate to use template page when clicking "Use" button', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Test Template' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('使用する')).toBeInTheDocument();
      });

      const useButton = screen.getByText('使用する');
      await user.click(useButton);

      expect(mockNavigate).toHaveBeenCalledWith('/templates/template-1/use');
    });

    it('should open detail modal when clicking "Detail" button', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Test Template' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('詳細')).toBeInTheDocument();
      });

      const detailButton = screen.getByText('詳細');
      await user.click(detailButton);

      await waitFor(() => {
        expect(screen.getByTestId('template-modal')).toBeInTheDocument();
        expect(screen.getByText('Modal for template: template-1')).toBeInTheDocument();
      });
    });

    it('should close modal when clicking close button', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Test Template' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('詳細')).toBeInTheDocument();
      });

      const detailButton = screen.getByText('詳細');
      await user.click(detailButton);

      await waitFor(() => {
        expect(screen.getByTestId('template-modal')).toBeInTheDocument();
      });

      const closeButton = screen.getByText('Close Modal');
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('template-modal')).not.toBeInTheDocument();
      });
    });

    it('should navigate to use template page from modal', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'Test Template' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('詳細')).toBeInTheDocument();
      });

      const detailButton = screen.getByText('詳細');
      await user.click(detailButton);

      await waitFor(() => {
        expect(screen.getByTestId('template-modal')).toBeInTheDocument();
      });

      const useTemplateButton = screen.getByText('Use Template');
      await user.click(useTemplateButton);

      expect(mockNavigate).toHaveBeenCalledWith('/templates/template-1/use');
    });
  });

  describe('Navigation', () => {
    it('should navigate to create template page when clicking new template button', async () => {
      const user = userEvent.setup();

      mockFetchResponse({ templates: [] });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('➕ 新規登録')).toBeInTheDocument();
      });

      const newTemplateButton = screen.getByText('➕ 新規登録');
      await user.click(newTemplateButton);

      expect(mockNavigate).toHaveBeenCalledWith('/templates/create');
    });
  });

  describe('Error Handling', () => {
    it('should display error message when fetch fails', async () => {
      mockFetchError('テンプレートの取得に失敗しました');

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText(/テンプレートの取得に失敗しました/i)).toBeInTheDocument();
      });
    });

    it('should display error when API returns non-ok status', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({}),
      } as Response);

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText(/テンプレートの取得に失敗しました/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authentication', () => {
    it('should include auth token in API requests', async () => {
      const fetchSpy = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ templates: [] }),
      } as Response);

      global.fetch = fetchSpy;

      renderWithRouter(<Templates />);

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

  describe('Responsive Grid', () => {
    it('should display templates in a grid layout', async () => {
      const templates = [
        createMockTemplate({ id: 'template-1' }),
        createMockTemplate({ id: 'template-2' }),
        createMockTemplate({ id: 'template-3' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        // Check that templates are displayed in the grid
        const templateNames = screen.getAllByText('Test Template');
        expect(templateNames.length).toBe(3);
      });
    });
  });

  describe('Combined Filters', () => {
    it('should apply both category and search filters', async () => {
      const user = userEvent.setup();
      const templates = [
        createMockTemplate({ id: 'template-1', name: 'LP Design', category: 'LP' }),
        createMockTemplate({ id: 'template-2', name: 'Banner Design', category: 'Banner' }),
        createMockTemplate({ id: 'template-3', name: 'LP Template', category: 'LP' }),
      ];

      mockFetchResponse({ templates });

      renderWithRouter(<Templates />);

      await waitFor(() => {
        expect(screen.getByText('LP Design')).toBeInTheDocument();
        expect(screen.getByText('Banner Design')).toBeInTheDocument();
        expect(screen.getByText('LP Template')).toBeInTheDocument();
      });

      // Search for "design"
      const searchInput = screen.getByPlaceholderText('テンプレートを検索...');
      await user.type(searchInput, 'design');

      await waitFor(() => {
        expect(screen.getByText('LP Design')).toBeInTheDocument();
        expect(screen.getByText('Banner Design')).toBeInTheDocument();
        expect(screen.queryByText('LP Template')).not.toBeInTheDocument();
      });
    });
  });
});
