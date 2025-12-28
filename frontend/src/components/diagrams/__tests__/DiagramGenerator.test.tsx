/**
 * Unit tests for DiagramGenerator component
 */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, userEvent } from '@/__tests__/utils/test-utils';
import { DiagramGenerator } from '../DiagramGenerator';
import { useGenerateSequenceDiagram, useGenerateAuthFlowDiagram } from '@/hooks/useDiagrams';
import { mockDiagramResponse, mockAuthFlowDiagram } from '@/__tests__/mocks/data';

// Mock the hooks
jest.mock('@/hooks/useDiagrams');
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));
jest.mock('../MermaidViewer', () => ({
  MermaidViewer: ({ code, title }: any) => (
    <div data-testid="mermaid-viewer">
      <div>{title}</div>
      <pre>{code}</pre>
    </div>
  ),
}));

const mockUseGenerateSequenceDiagram = useGenerateSequenceDiagram as jest.MockedFunction<
  typeof useGenerateSequenceDiagram
>;
const mockUseGenerateAuthFlowDiagram = useGenerateAuthFlowDiagram as jest.MockedFunction<
  typeof useGenerateAuthFlowDiagram
>;

describe('DiagramGenerator', () => {
  const mockSequenceMutate = jest.fn();
  const mockAuthMutate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseGenerateSequenceDiagram.mockReturnValue({
      mutate: mockSequenceMutate,
      isPending: false,
      isError: false,
      isSuccess: false,
    } as any);

    mockUseGenerateAuthFlowDiagram.mockReturnValue({
      mutate: mockAuthMutate,
      isPending: false,
      isError: false,
      isSuccess: false,
    } as any);
  });

  describe('Rendering', () => {
    it('should render the diagram generator form', () => {
      renderWithProviders(<DiagramGenerator />);

      expect(screen.getByText('Generate Diagram')).toBeInTheDocument();
      expect(screen.getByLabelText(/diagram type/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /generate diagram/i })).toBeInTheDocument();
    });

    it('should show sequence diagram options by default', () => {
      renderWithProviders(<DiagramGenerator />);

      expect(screen.getByLabelText(/endpoint document id/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/enter document id from search results/i)
      ).toBeInTheDocument();
    });

    it('should not show auth flow options by default', () => {
      renderWithProviders(<DiagramGenerator />);

      expect(screen.queryByLabelText(/authentication type/i)).not.toBeInTheDocument();
    });
  });

  describe('Diagram Type Selection', () => {
    it('should switch to auth flow options when selected', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      // Click the diagram type select
      const diagramTypeSelect = screen.getByLabelText(/diagram type/i);
      await user.click(diagramTypeSelect);

      // Select "Authentication Flow"
      const authOption = screen.getByText('Authentication Flow');
      await user.click(authOption);

      // Auth type select should now be visible
      await waitFor(() => {
        expect(screen.getByLabelText(/authentication type/i)).toBeInTheDocument();
      });

      // Endpoint ID input should not be visible
      expect(screen.queryByLabelText(/endpoint document id/i)).not.toBeInTheDocument();
    });

    it('should switch back to sequence diagram options', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      // First switch to auth
      const diagramTypeSelect = screen.getByLabelText(/diagram type/i);
      await user.click(diagramTypeSelect);
      const authOption = screen.getByText('Authentication Flow');
      await user.click(authOption);

      await waitFor(() => {
        expect(screen.getByLabelText(/authentication type/i)).toBeInTheDocument();
      });

      // Then switch back to sequence
      await user.click(diagramTypeSelect);
      const sequenceOption = screen.getByText('Sequence Diagram');
      await user.click(sequenceOption);

      await waitFor(() => {
        expect(screen.getByLabelText(/endpoint document id/i)).toBeInTheDocument();
      });

      expect(screen.queryByLabelText(/authentication type/i)).not.toBeInTheDocument();
    });
  });

  describe('Sequence Diagram Generation', () => {
    it('should update endpoint ID input', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      const endpointInput = screen.getByLabelText(/endpoint document id/i) as HTMLInputElement;
      await user.type(endpointInput, 'test-endpoint-123');

      expect(endpointInput.value).toBe('test-endpoint-123');
    });

    it('should show error toast when endpoint ID is empty', async () => {
      const user = userEvent.setup();
      const mockToast = jest.fn();

      jest.mocked(require('@/hooks/use-toast').useToast).mockReturnValue({
        toast: mockToast,
      });

      renderWithProviders(<DiagramGenerator />);

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      await user.click(generateButton);

      expect(mockToast).toHaveBeenCalledWith({
        title: 'Endpoint ID required',
        description: 'Please enter an endpoint document ID',
        variant: 'destructive',
      });

      expect(mockSequenceMutate).not.toHaveBeenCalled();
    });

    it('should generate sequence diagram with valid endpoint ID', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      const endpointInput = screen.getByLabelText(/endpoint document id/i);
      await user.type(endpointInput, 'test-endpoint-123');

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      await user.click(generateButton);

      expect(mockSequenceMutate).toHaveBeenCalledWith(
        { endpoint_id: 'test-endpoint-123' },
        expect.any(Object)
      );
    });

    it('should not generate diagram when endpoint ID is whitespace', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      const endpointInput = screen.getByLabelText(/endpoint document id/i);
      await user.type(endpointInput, '   ');

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      await user.click(generateButton);

      expect(mockSequenceMutate).not.toHaveBeenCalled();
    });
  });

  describe('Auth Flow Diagram Generation', () => {
    it('should generate auth flow diagram with default bearer type', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      // Switch to auth flow
      const diagramTypeSelect = screen.getByLabelText(/diagram type/i);
      await user.click(diagramTypeSelect);
      const authOption = screen.getByText('Authentication Flow');
      await user.click(authOption);

      await waitFor(() => {
        expect(screen.getByLabelText(/authentication type/i)).toBeInTheDocument();
      });

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      await user.click(generateButton);

      expect(mockAuthMutate).toHaveBeenCalledWith(
        { auth_type: 'bearer' },
        expect.any(Object)
      );
    });

    it('should generate auth flow diagram with oauth2 type', async () => {
      const user = userEvent.setup();
      renderWithProviders(<DiagramGenerator />);

      // Switch to auth flow
      const diagramTypeSelect = screen.getByLabelText(/diagram type/i);
      await user.click(diagramTypeSelect);
      const authOption = screen.getByText('Authentication Flow');
      await user.click(authOption);

      await waitFor(() => {
        expect(screen.getByLabelText(/authentication type/i)).toBeInTheDocument();
      });

      // Select OAuth 2.0
      const authTypeSelect = screen.getByLabelText(/authentication type/i);
      await user.click(authTypeSelect);
      const oauth2Option = screen.getByText('OAuth 2.0');
      await user.click(oauth2Option);

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      await user.click(generateButton);

      expect(mockAuthMutate).toHaveBeenCalledWith(
        { auth_type: 'oauth2' },
        expect.any(Object)
      );
    });
  });

  describe('Loading States', () => {
    it('should disable button when generating sequence diagram', () => {
      mockUseGenerateSequenceDiagram.mockReturnValue({
        mutate: mockSequenceMutate,
        isPending: true,
        isError: false,
        isSuccess: false,
      } as any);

      renderWithProviders(<DiagramGenerator />);

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      expect(generateButton).toBeDisabled();
    });

    it('should disable button when generating auth flow diagram', () => {
      mockUseGenerateAuthFlowDiagram.mockReturnValue({
        mutate: mockAuthMutate,
        isPending: true,
        isError: false,
        isSuccess: false,
      } as any);

      renderWithProviders(<DiagramGenerator />);

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      expect(generateButton).toBeDisabled();
    });

    it('should show loading spinner when generating', () => {
      mockUseGenerateSequenceDiagram.mockReturnValue({
        mutate: mockSequenceMutate,
        isPending: true,
        isError: false,
        isSuccess: false,
      } as any);

      renderWithProviders(<DiagramGenerator />);

      const loadingSpinner = document.querySelector('.animate-spin');
      expect(loadingSpinner).toBeInTheDocument();
    });
  });

  describe('Diagram Display', () => {
    it('should not show MermaidViewer initially', () => {
      renderWithProviders(<DiagramGenerator />);

      expect(screen.queryByTestId('mermaid-viewer')).not.toBeInTheDocument();
    });

    it('should display MermaidViewer when diagram is generated', async () => {
      const user = userEvent.setup();

      // Setup mock to call onSuccess callback
      mockSequenceMutate.mockImplementation((request, callbacks) => {
        callbacks?.onSuccess?.(mockDiagramResponse);
      });

      renderWithProviders(<DiagramGenerator />);

      const endpointInput = screen.getByLabelText(/endpoint document id/i);
      await user.type(endpointInput, 'test-endpoint-123');

      const generateButton = screen.getByRole('button', { name: /generate diagram/i });
      await user.click(generateButton);

      await waitFor(() => {
        expect(screen.getByTestId('mermaid-viewer')).toBeInTheDocument();
      });

      expect(screen.getByText('User API Sequence')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels for form inputs', () => {
      renderWithProviders(<DiagramGenerator />);

      expect(screen.getByLabelText(/diagram type/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/endpoint document id/i)).toBeInTheDocument();
    });

    it('should have accessible button text', () => {
      renderWithProviders(<DiagramGenerator />);

      expect(screen.getByRole('button', { name: /generate diagram/i })).toBeInTheDocument();
    });
  });
});
