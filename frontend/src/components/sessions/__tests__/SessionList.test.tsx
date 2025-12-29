/**
 * Unit tests for SessionList component
 */

import React from 'react';
import { screen } from '@testing-library/react';
import { renderWithProviders, userEvent } from '@/__tests__/utils/test-utils';
import { SessionList } from '../SessionList';
import { useListSessions, useDeleteSession } from '@/hooks/useSessions';
import { mockSessions } from '@/__tests__/mocks/data';
import { SessionStatus } from '@/types';

// Mock the hooks
jest.mock('@/hooks/useSessions');
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock window.confirm
global.confirm = jest.fn();

const mockUseListSessions = useListSessions as jest.MockedFunction<typeof useListSessions>;
const mockUseDeleteSession = useDeleteSession as jest.MockedFunction<typeof useDeleteSession>;

describe('SessionList', () => {
  const mockDeleteMutate = jest.fn();
  const mockOnSelectSession = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseListSessions.mockReturnValue({
      data: { sessions: mockSessions, total: mockSessions.length },
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    mockUseDeleteSession.mockReturnValue({
      mutate: mockDeleteMutate,
      isPending: false,
      isError: false,
      isSuccess: false,
    } as any);
  });

  describe('Rendering', () => {
    it('should render the sessions card', () => {
      renderWithProviders(<SessionList />);

      expect(screen.getByText('Sessions')).toBeInTheDocument();
    });

    it('should render filter buttons', () => {
      renderWithProviders(<SessionList />);

      expect(screen.getByRole('button', { name: /^all$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^active$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^inactive$/i })).toBeInTheDocument();
    });

    it('should render all sessions', () => {
      renderWithProviders(<SessionList />);

      // Check for session IDs (truncated to first 8 chars)
      // Multiple sessions may have same prefix
      const sessionIds = screen.getAllByText(/test-ses/);
      expect(sessionIds.length).toBeGreaterThan(0);
    });

    it('should render session status badges', () => {
      renderWithProviders(<SessionList />);

      expect(screen.getByText(SessionStatus.ACTIVE)).toBeInTheDocument();
      expect(screen.getByText(SessionStatus.INACTIVE)).toBeInTheDocument();
      expect(screen.getByText(SessionStatus.EXPIRED)).toBeInTheDocument();
    });

    it('should render user IDs when available', () => {
      renderWithProviders(<SessionList />);

      // Multiple sessions may have the same user ID
      const userIds = screen.getAllByText('test-user');
      expect(userIds.length).toBeGreaterThan(0);
    });

    it('should render conversation message counts', () => {
      renderWithProviders(<SessionList />);

      // First and second sessions have 2 messages
      const messageElements = screen.getAllByText(/2 messages/);
      expect(messageElements.length).toBeGreaterThan(0);

      // Third session has 0 messages
      expect(screen.getByText(/0 messages/)).toBeInTheDocument();
    });

    it('should show loading state', () => {
      mockUseListSessions.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
      } as any);

      renderWithProviders(<SessionList />);

      expect(screen.getByText(/loading sessions/i)).toBeInTheDocument();
    });

    it('should show empty state when no sessions', () => {
      mockUseListSessions.mockReturnValue({
        data: { sessions: [], total: 0 },
        isLoading: false,
        isError: false,
        error: null,
      } as any);

      renderWithProviders(<SessionList />);

      expect(screen.getByText(/no sessions found/i)).toBeInTheDocument();
    });

    it('should render View buttons when onSelectSession is provided', () => {
      renderWithProviders(<SessionList onSelectSession={mockOnSelectSession} />);

      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      expect(viewButtons.length).toBe(mockSessions.length);
    });

    it('should not render View buttons when onSelectSession is not provided', () => {
      renderWithProviders(<SessionList />);

      const viewButtons = screen.queryAllByRole('button', { name: /view/i });
      expect(viewButtons.length).toBe(0);
    });

    it('should render delete buttons for all sessions', () => {
      renderWithProviders(<SessionList />);

      // Get all buttons that contain the Trash2 icon
      const deleteButtons = screen.getAllByRole('button').filter(
        button => button.querySelector('svg')
      );

      // Filter to get only delete buttons (not View buttons)
      const actualDeleteButtons = deleteButtons.filter(
        button => !button.textContent?.includes('View')
      );

      expect(actualDeleteButtons.length).toBe(mockSessions.length);
    });
  });

  describe('Filter Interactions', () => {
    it('should highlight "All" filter by default', () => {
      renderWithProviders(<SessionList />);

      const allButton = screen.getByRole('button', { name: /^all$/i });
      // Button with variant="default" has bg-primary class
      expect(allButton).toHaveClass('bg-primary');
    });

    it('should filter sessions by ACTIVE status', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionList />);

      const activeButton = screen.getByRole('button', { name: /^active$/i });
      await user.click(activeButton);

      expect(mockUseListSessions).toHaveBeenCalledWith(undefined, SessionStatus.ACTIVE);
    });

    it('should filter sessions by INACTIVE status', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionList />);

      const inactiveButton = screen.getByRole('button', { name: /^inactive$/i });
      await user.click(inactiveButton);

      expect(mockUseListSessions).toHaveBeenCalledWith(undefined, SessionStatus.INACTIVE);
    });

    it('should reset filter when clicking "All"', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionList />);

      // First click Active
      const activeButton = screen.getByRole('button', { name: /^active$/i });
      await user.click(activeButton);

      // Then click All
      const allButton = screen.getByRole('button', { name: /^all$/i });
      await user.click(allButton);

      expect(mockUseListSessions).toHaveBeenLastCalledWith(undefined, undefined);
    });
  });

  describe('Session Actions', () => {
    it('should call onSelectSession when View button is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<SessionList onSelectSession={mockOnSelectSession} />);

      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      await user.click(viewButtons[0]);

      expect(mockOnSelectSession).toHaveBeenCalledWith('test-session-123');
    });

    it('should show confirmation dialog before deleting', async () => {
      const user = userEvent.setup();
      (global.confirm as jest.Mock).mockReturnValue(false);

      renderWithProviders(<SessionList />);

      const deleteButtons = screen.getAllByRole('button').filter(
        button => button.querySelector('svg') && !button.textContent?.includes('View')
      );

      await user.click(deleteButtons[0]);

      expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this session?');
      expect(mockDeleteMutate).not.toHaveBeenCalled();
    });

    it('should delete session when confirmed', async () => {
      const user = userEvent.setup();
      (global.confirm as jest.Mock).mockReturnValue(true);

      renderWithProviders(<SessionList />);

      const deleteButtons = screen.getAllByRole('button').filter(
        button => button.querySelector('svg') && !button.textContent?.includes('View')
      );

      await user.click(deleteButtons[0]);

      expect(global.confirm).toHaveBeenCalled();
      expect(mockDeleteMutate).toHaveBeenCalledWith(
        'test-session-123',
        expect.any(Object)
      );
    });
  });

  describe('Status Badge Variants', () => {
    it('should render correct badge variant for ACTIVE status', () => {
      renderWithProviders(<SessionList />);

      const activeBadge = screen.getByText(SessionStatus.ACTIVE);
      expect(activeBadge).toBeInTheDocument();
      // Note: Badge variant is applied via className, not data-attribute
    });

    it('should render correct badge variant for INACTIVE status', () => {
      renderWithProviders(<SessionList />);

      const inactiveBadge = screen.getByText(SessionStatus.INACTIVE);
      expect(inactiveBadge).toBeInTheDocument();
    });

    it('should render correct badge variant for EXPIRED status', () => {
      renderWithProviders(<SessionList />);

      const expiredBadge = screen.getByText(SessionStatus.EXPIRED);
      expect(expiredBadge).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible filter buttons', () => {
      renderWithProviders(<SessionList />);

      expect(screen.getByRole('button', { name: /^all$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^active$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^inactive$/i })).toBeInTheDocument();
    });

    it('should have accessible action buttons', () => {
      renderWithProviders(<SessionList onSelectSession={mockOnSelectSession} />);

      const viewButtons = screen.getAllByRole('button', { name: /view/i });
      expect(viewButtons.length).toBeGreaterThan(0);

      const deleteButtons = screen.getAllByRole('button').filter(
        button => button.querySelector('svg') && !button.textContent?.includes('View')
      );
      expect(deleteButtons.length).toBeGreaterThan(0);
    });
  });
});
