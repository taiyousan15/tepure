/**
 * Dashboard component tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import Dashboard from '../../src/pages/Dashboard';
import {
  renderWithRouter,
  mockFetchResponse,
  mockFetchError,
  setAuthToken,
  clearLocalStorage,
  createMockTemplate,
  createMockJob,
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

describe('Dashboard Component', () => {
  beforeEach(() => {
    clearLocalStorage();
    setAuthToken('test-token');
    mockNavigate.mockClear();
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render dashboard with loading state initially', () => {
      renderWithRouter(<Dashboard />);
      expect(screen.getByText('読み込み中...')).toBeInTheDocument();
    });

    it('should render dashboard title and description', async () => {
      mockFetchResponse({
        templates: [],
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('ダッシュボード')).toBeInTheDocument();
        expect(screen.getByText('Figma Template Automation へようこそ')).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('should fetch and display dashboard statistics', async () => {
      const templates = [
        createMockTemplate({ id: 'template-1' }),
        createMockTemplate({ id: 'template-2' }),
      ];

      const jobs = [
        createMockJob({ job_id: 'job-1', status: 'completed' }),
        createMockJob({ job_id: 'job-2', status: 'pending' }),
        createMockJob({ job_id: 'job-3', status: 'processing' }),
      ];

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        const statValues = screen.getAllByText('2');
        expect(statValues.length).toBeGreaterThanOrEqual(2); // Total templates and pending jobs
        expect(screen.getByText('1')).toBeInTheDocument(); // Completed jobs
        expect(screen.getByText('3')).toBeInTheDocument(); // Total jobs
      });
    });

    it('should display error message when template fetch fails', async () => {
      mockFetchError('データの取得に失敗しました');

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/データの取得に失敗しました/i)).toBeInTheDocument();
      });
    });

    it('should display error message when jobs fetch fails', async () => {
      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: false,
            json: async () => ({}),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/ジョブデータの取得に失敗しました/i)).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Cards', () => {
    it('should display all four statistics cards', async () => {
      mockFetchResponse({
        templates: [createMockTemplate()],
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('テンプレート')).toBeInTheDocument();
        expect(screen.getByText('完了ジョブ')).toBeInTheDocument();
        expect(screen.getByText('待機中')).toBeInTheDocument();
        expect(screen.getByText('総ジョブ数')).toBeInTheDocument();
      });
    });

    it('should show zero statistics when no data', async () => {
      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs: [] }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        const statValues = screen.getAllByText('0');
        expect(statValues.length).toBeGreaterThanOrEqual(4); // All four stats should show 0
      });
    });
  });

  describe('Quick Actions', () => {
    it('should display quick action buttons', async () => {
      mockFetchResponse({
        templates: [],
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('クイックアクション')).toBeInTheDocument();
        expect(screen.getByText('テンプレートを使用')).toBeInTheDocument();
        expect(screen.getByText('新規テンプレート登録')).toBeInTheDocument();
      });
    });

    it('should navigate to templates page when clicking "Use Template"', async () => {
      const user = userEvent.setup();

      mockFetchResponse({
        templates: [],
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('テンプレートを使用')).toBeInTheDocument();
      });

      const useTemplateButton = screen.getByText('テンプレートを使用').closest('button');
      if (useTemplateButton) {
        await user.click(useTemplateButton);
        expect(mockNavigate).toHaveBeenCalledWith('/templates');
      }
    });

    it('should navigate to create template page when clicking "New Template"', async () => {
      const user = userEvent.setup();

      mockFetchResponse({
        templates: [],
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('新規テンプレート登録')).toBeInTheDocument();
      });

      const newTemplateButton = screen.getByText('新規テンプレート登録').closest('button');
      if (newTemplateButton) {
        await user.click(newTemplateButton);
        expect(mockNavigate).toHaveBeenCalledWith('/templates/create');
      }
    });
  });

  describe('Recent Jobs Section', () => {
    it('should display empty state when no jobs exist', async () => {
      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs: [] }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('まだジョブがありません')).toBeInTheDocument();
        expect(screen.getByText('テンプレートから開始')).toBeInTheDocument();
      });
    });

    it('should display recent jobs table with data', async () => {
      const jobs = [
        createMockJob({
          job_id: 'job-1',
          template_id: 'template-1',
          status: 'completed',
          created_at: '2025-01-01T10:00:00Z',
        }),
        createMockJob({
          job_id: 'job-2',
          template_id: 'template-2',
          status: 'pending',
          created_at: '2025-01-01T11:00:00Z',
        }),
      ];

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('最近のジョブ')).toBeInTheDocument();
        expect(screen.getByText('job-1')).toBeInTheDocument();
        expect(screen.getByText('job-2')).toBeInTheDocument();
        expect(screen.getByText('template-1')).toBeInTheDocument();
        expect(screen.getByText('template-2')).toBeInTheDocument();
      });
    });

    it('should display correct status badges', async () => {
      const jobs = [
        createMockJob({ job_id: 'job-1', status: 'completed' }),
        createMockJob({ job_id: 'job-2', status: 'pending' }),
        createMockJob({ job_id: 'job-3', status: 'processing' }),
        createMockJob({ job_id: 'job-4', status: 'failed' }),
      ];

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('完了')).toBeInTheDocument();
        const waitingBadges = screen.getAllByText('待機中');
        expect(waitingBadges.length).toBeGreaterThan(0);
        expect(screen.getByText('処理中')).toBeInTheDocument();
        expect(screen.getByText('失敗')).toBeInTheDocument();
      });
    });

    it('should limit recent jobs to 5 items', async () => {
      const jobs = Array.from({ length: 10 }, (_, i) =>
        createMockJob({ job_id: `job-${i + 1}` })
      );

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('job-1')).toBeInTheDocument();
        expect(screen.getByText('job-5')).toBeInTheDocument();
        expect(screen.queryByText('job-6')).not.toBeInTheDocument();
      });
    });

    it('should navigate to jobs page when clicking "View All"', async () => {
      const user = userEvent.setup();

      const jobs = [createMockJob({ job_id: 'job-1' })];

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('すべて見る →')).toBeInTheDocument();
      });

      const viewAllButton = screen.getByText('すべて見る →');
      await user.click(viewAllButton);
      expect(mockNavigate).toHaveBeenCalledWith('/jobs');
    });
  });

  describe('Navigation', () => {
    it('should navigate to templates list when clicking "View Templates"', async () => {
      const user = userEvent.setup();

      mockFetchResponse({
        templates: [createMockTemplate()],
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText('一覧を見る →')).toBeInTheDocument();
      });

      const viewTemplatesButton = screen.getByText('一覧を見る →');
      await user.click(viewTemplatesButton);
      expect(mockNavigate).toHaveBeenCalledWith('/templates');
    });
  });

  describe('Date Formatting', () => {
    it('should format dates correctly', async () => {
      const job = createMockJob({
        job_id: 'job-1',
        created_at: '2025-01-15T14:30:00Z',
      });

      global.fetch = vi.fn((url: string | URL) => {
        const urlStr = url.toString();
        if (urlStr.includes('/api/v1/templates')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ templates: [] }),
          } as Response);
        }
        if (urlStr.includes('/api/v1/jobs')) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ jobs: [job] }),
          } as Response);
        }
        return Promise.reject(new Error('Unknown URL'));
      });

      renderWithRouter(<Dashboard />);

      await waitFor(() => {
        // Date should be formatted as Japanese locale
        const dateElements = screen.getAllByText(/2025/);
        expect(dateElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Authentication', () => {
    it('should include auth token in API requests', async () => {
      const fetchSpy = vi.fn((url: string | URL) => {
        return Promise.resolve({
          ok: true,
          json: async () => ({ templates: [], jobs: [] }),
        } as Response);
      });

      global.fetch = fetchSpy;

      renderWithRouter(<Dashboard />);

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
});
