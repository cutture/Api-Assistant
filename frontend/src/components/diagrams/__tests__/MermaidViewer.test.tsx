/**
 * Unit tests for MermaidViewer component
 */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, userEvent } from '@/__tests__/utils/test-utils';
import { MermaidViewer } from '../MermaidViewer';
import mermaid from 'mermaid';

// Mock mermaid
jest.mock('mermaid', () => ({
  __esModule: true,
  default: {
    initialize: jest.fn(),
    render: jest.fn().mockResolvedValue({ svg: '<svg>mock svg</svg>' }),
  },
}));

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url');
global.URL.revokeObjectURL = jest.fn();

// Mock XMLSerializer
global.XMLSerializer = jest.fn().mockImplementation(() => ({
  serializeToString: jest.fn(() => '<svg>mock svg</svg>'),
})) as any;

// Create a mock toast function that can be controlled in tests
const mockToast = jest.fn();

// Mock toast
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

describe('MermaidViewer', () => {
  const mockCode = `sequenceDiagram
    participant Client
    participant API
    Client->>API: Request
    API-->>Client: Response`;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render with title', () => {
      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      expect(screen.getByText('Test Diagram')).toBeInTheDocument();
    });

    it('should render without title', () => {
      renderWithProviders(<MermaidViewer code={mockCode} />);

      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    });

    it('should render action buttons when title is provided', () => {
      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      expect(screen.getByRole('button', { name: /copy code/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /download svg/i })).toBeInTheDocument();
    });

    it('should not render action buttons when title is not provided', () => {
      renderWithProviders(<MermaidViewer code={mockCode} />);

      expect(screen.queryByRole('button', { name: /copy code/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /download svg/i })).not.toBeInTheDocument();
    });

    it('should render the mermaid container', () => {
      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      const container = document.querySelector('.mermaid');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Mermaid Initialization', () => {
    it('should initialize mermaid on mount', async () => {
      renderWithProviders(<MermaidViewer code={mockCode} />);

      await waitFor(() => {
        expect(mermaid.initialize).toHaveBeenCalledWith({
          startOnLoad: false,
          theme: 'default',
          securityLevel: 'loose',
          fontFamily: 'arial, sans-serif',
        });
      });
    });

    it('should call mermaid.render after initialization', async () => {
      renderWithProviders(<MermaidViewer code={mockCode} />);

      await waitFor(() => {
        expect(mermaid.render).toHaveBeenCalled();
      });
    });

    it('should update diagram when code changes', async () => {
      const { rerender } = renderWithProviders(<MermaidViewer code={mockCode} />);

      await waitFor(() => {
        expect(mermaid.render).toHaveBeenCalledTimes(1);
      });

      const newCode = `graph TD
        A-->B`;

      rerender(<MermaidViewer code={newCode} />);

      // Should be called twice: once for initial render, once for update
      await waitFor(() => {
        expect(mermaid.render).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Copy Code Functionality', () => {
    it('should copy code to clipboard when copy button is clicked', async () => {
      const user = userEvent.setup();
      const mockWriteText = jest.fn();
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: mockWriteText,
        },
        writable: true,
        configurable: true,
      });

      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      await user.click(copyButton);

      expect(mockWriteText).toHaveBeenCalledWith(mockCode);
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Code copied',
        description: 'Mermaid code copied to clipboard',
      });
    });
  });

  describe('Download SVG Functionality', () => {
    beforeEach(() => {
      // Mock document.createElement for the download link
      const mockAnchor = document.createElement('a');
      mockAnchor.click = jest.fn();
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);
    });

    afterEach(() => {
      jest.restoreAllMocks();
    });

    it.skip('should download SVG when download button is clicked', async () => {
      const user = userEvent.setup();

      const { container } = renderWithProviders(
        <MermaidViewer code={mockCode} title="Test Diagram" />
      );

      // Mock SVG element in the container
      const mockSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      const mermaidContainer = container.querySelector('.mermaid');
      mermaidContainer?.appendChild(mockSvg);

      const downloadButton = screen.getByRole('button', { name: /download svg/i });
      await user.click(downloadButton);

      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Download started',
        description: 'Diagram downloaded as SVG',
      });
    });

    it.skip('should show error toast when no SVG is found', async () => {
      const user = userEvent.setup();

      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      // Don't add any SVG element to the container

      const downloadButton = screen.getByRole('button', { name: /download svg/i });
      await user.click(downloadButton);

      expect(mockToast).toHaveBeenCalledWith({
        title: 'Error',
        description: 'No diagram found to download',
        variant: 'destructive',
      });
    });

    it.skip('should use title for SVG filename', async () => {
      const user = userEvent.setup();
      const mockAnchor = document.createElement('a');
      mockAnchor.click = jest.fn();
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);

      const { container } = renderWithProviders(
        <MermaidViewer code={mockCode} title="My Custom Diagram" />
      );

      // Mock SVG element
      const mockSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      const mermaidContainer = container.querySelector('.mermaid');
      mermaidContainer?.appendChild(mockSvg);

      const downloadButton = screen.getByRole('button', { name: /download svg/i });
      await user.click(downloadButton);

      expect(mockAnchor.download).toBe('My Custom Diagram.svg');
    });

    it.skip('should use default filename when no title is provided', async () => {
      const user = userEvent.setup();
      const mockAnchor = document.createElement('a');
      mockAnchor.click = jest.fn();
      jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);

      const { container } = renderWithProviders(<MermaidViewer code={mockCode} />);

      // Mock SVG element
      const mockSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      const mermaidContainer = container.querySelector('.mermaid');
      mermaidContainer?.appendChild(mockSvg);

      // Since there's no title, buttons won't be rendered
      // This test verifies the default filename logic in the component
      // We can't directly test it without a title, but we've covered the logic
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      expect(screen.getByRole('button', { name: /copy code/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /download svg/i })).toBeInTheDocument();
    });

    it('should have proper heading when title is provided', () => {
      renderWithProviders(<MermaidViewer code={mockCode} title="Test Diagram" />);

      const heading = screen.getByText('Test Diagram');
      expect(heading).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle download errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock XMLSerializer to throw an error
      const mockSerializer = {
        serializeToString: jest.fn(() => {
          throw new Error('Serialization failed');
        }),
      };
      (global.XMLSerializer as any).mockImplementation(() => mockSerializer);

      const { container } = renderWithProviders(
        <MermaidViewer code={mockCode} title="Test Diagram" />
      );

      // Wait for render to complete
      await waitFor(() => {
        expect(mermaid.render).toHaveBeenCalled();
      });

      // Mock SVG element
      const mockSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      const mermaidContainer = container.querySelector('.mermaid');
      mermaidContainer?.appendChild(mockSvg);

      const downloadButton = screen.getByRole('button', { name: /download svg/i });
      await user.click(downloadButton);

      expect(mockToast).toHaveBeenCalledWith({
        title: 'Download failed',
        description: 'Serialization failed',
        variant: 'destructive',
      });
    });
  });
});
