/**
 * Unit tests for SessionManager component
 */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, userEvent } from '@/__tests__/utils/test-utils';
import { SessionManager } from '../SessionManager';
import { useCreateSession, useSessionStats } from '@/hooks/useSessions';
import { mockSession, mockSessionStats } from '@/__tests__/mocks/data';

// Mock the hooks
jest.mock('@/hooks/useSessions');
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

const mockUseCreateSession = useCreateSession as jest.MockedFunction<typeof useCreateSession>;
const mockUseSessionStats = useSessionStats as jest.MockedFunction<typeof useSessionStats>;

describe('SessionManager', () => {
  const mockMutate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseCreateSession.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: false,
      isSuccess: false,
      data: undefined,
      error: null,
      reset: jest.fn(),
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      isIdle: true,
      isPaused: false,
      status: 'idle',
      submittedAt: 0,
      mutateAsync: jest.fn(),
    });

    mockUseSessionStats.mockReturnValue({
      data: mockSessionStats,
      isLoading: false,
      isError: false,
      error: null,
      refetch: jest.fn(),
      isSuccess: true,
      status: 'success',
      dataUpdatedAt: 0,
      errorUpdatedAt: 0,
      failureCount: 0,
      failureReason: null,
      errorUpdateCount: 0,
      isFetched: true,
      isFetchedAfterMount: true,
      isFetching: false,
      isInitialLoading: false,
      isLoadingError: false,
      isPaused: false,
      isPlaceholderData: false,
      isPreviousData: false,
      isRefetchError: false,
      isRefetching: false,
      isStale: false,
      fetchStatus: 'idle',
      promise: Promise.resolve(mockSessionStats),
    } as any);
  });

  describe('Rendering', () => {
    it('should render the session creation form', () => {
      renderWithProviders(<SessionManager />);

      expect(screen.getByText('Create New Session')).toBeInTheDocument();
      expect(screen.getByLabelText(/user id/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/session ttl/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create session/i })).toBeInTheDocument();
    });

    it('should render session stats when available', () => {
      renderWithProviders(<SessionManager />);

      expect(screen.getByText('Total Sessions')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Inactive')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('Expired')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should not render stats when unavailable', () => {
      mockUseSessionStats.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as any);

      renderWithProviders(<SessionManager />);

      expect(screen.queryByText('Total Sessions')).not.toBeInTheDocument();
    });
  });

  describe('Form Interactions', () => {
    it('should update user ID input', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      const userIdInput = screen.getByLabelText(/user id/i) as HTMLInputElement;
      await user.type(userIdInput, 'test-user-123');

      expect(userIdInput.value).toBe('test-user-123');
    });

    it('should update TTL input', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      const ttlInput = screen.getByLabelText(/session ttl/i) as HTMLInputElement;
      await user.clear(ttlInput);
      await user.type(ttlInput, '120');

      expect(ttlInput.value).toBe('120');
    });

    it('should toggle reranking checkbox', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      const rerankingCheckbox = screen.getByLabelText(/enable re-ranking/i) as HTMLInputElement;
      expect(rerankingCheckbox).not.toBeChecked();

      await user.click(rerankingCheckbox);
      expect(rerankingCheckbox).toBeChecked();
    });

    it('should toggle query expansion checkbox', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      const queryExpansionCheckbox = screen.getByLabelText(/enable query expansion/i) as HTMLInputElement;
      expect(queryExpansionCheckbox).not.toBeChecked();

      await user.click(queryExpansionCheckbox);
      expect(queryExpansionCheckbox).toBeChecked();
    });
  });

  describe('Session Creation', () => {
    it('should call createSession with correct parameters', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      // Fill in form
      const userIdInput = screen.getByLabelText(/user id/i);
      await user.type(userIdInput, 'test-user');

      const ttlInput = screen.getByLabelText(/session ttl/i);
      await user.clear(ttlInput);
      await user.type(ttlInput, '90');

      const rerankingCheckbox = screen.getByLabelText(/enable re-ranking/i);
      await user.click(rerankingCheckbox);

      // Submit form
      const createButton = screen.getByRole('button', { name: /create session/i });
      await user.click(createButton);

      expect(mockMutate).toHaveBeenCalledWith(
        {
          user_id: 'test-user',
          ttl_minutes: 90,
          settings: {
            default_search_mode: 'hybrid',
            default_n_results: 10,
            use_reranking: true,
            use_query_expansion: false,
            use_diversification: false,
            show_scores: true,
            show_metadata: true,
            max_content_length: 500,
            custom_metadata: {},
          },
        },
        expect.any(Object)
      );
    });

    it('should handle empty user ID as undefined', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      const createButton = screen.getByRole('button', { name: /create session/i });
      await user.click(createButton);

      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: undefined,
        }),
        expect.any(Object)
      );
    });

    it('should disable button when creating session', () => {
      mockUseCreateSession.mockReturnValue({
        mutate: mockMutate,
        isPending: true,
        isError: false,
        isSuccess: false,
      } as any);

      renderWithProviders(<SessionManager />);

      const createButton = screen.getByRole('button', { name: /create session/i });
      expect(createButton).toBeDisabled();
    });

    it('should show loading spinner when creating session', () => {
      mockUseCreateSession.mockReturnValue({
        mutate: mockMutate,
        isPending: true,
        isError: false,
        isSuccess: false,
      } as any);

      renderWithProviders(<SessionManager />);

      const loadingSpinner = document.querySelector('.animate-spin');
      expect(loadingSpinner).toBeInTheDocument();
    });
  });

  describe('TTL Display', () => {
    it('should display correct hours and minutes for TTL', () => {
      renderWithProviders(<SessionManager />);

      // Default is 60 minutes (1 hour)
      expect(screen.getByText(/1 hours 0 minutes/i)).toBeInTheDocument();
    });

    it('should update hours and minutes display when TTL changes', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionManager />);

      const ttlInput = screen.getByLabelText(/session ttl/i);
      await user.clear(ttlInput);
      await user.type(ttlInput, '150');

      expect(screen.getByText(/2 hours 30 minutes/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels for form inputs', () => {
      renderWithProviders(<SessionManager />);

      expect(screen.getByLabelText(/user id/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/session ttl/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable re-ranking/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable query expansion/i)).toBeInTheDocument();
    });

    it('should have accessible button text', () => {
      renderWithProviders(<SessionManager />);

      expect(screen.getByRole('button', { name: /create session/i })).toBeInTheDocument();
    });
  });
});
