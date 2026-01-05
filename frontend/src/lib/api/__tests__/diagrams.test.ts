/**
 * Integration tests for diagram API client
 */

import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { generateSequenceDiagram, generateAuthFlowDiagram } from '../diagrams';
import { mockDiagramResponse, mockAuthFlowDiagram } from '@/__tests__/mocks/data';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create MSW server
const server = setupServer();

// Setup and teardown
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Diagram API Integration Tests', () => {
  describe('generateSequenceDiagram', () => {
    it('should generate sequence diagram successfully', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async () => {
          return HttpResponse.json(mockDiagramResponse);
        })
      );

      const result = await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
      });

      expect(result.data).toEqual(mockDiagramResponse);
      expect(result.error).toBeUndefined();
    });

    it('should handle invalid endpoint ID', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async () => {
          return HttpResponse.json(
            { detail: 'Endpoint document not found: invalid-id' },
            { status: 404 }
          );
        })
      );

      const result = await generateSequenceDiagram({
        endpoint_id: 'invalid-id',
      });

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
      expect(result.error).toContain('404');
    });

    it('should handle server errors during generation', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async () => {
          return HttpResponse.json(
            { detail: 'Internal server error during diagram generation' },
            { status: 500 }
          );
        })
      );

      const result = await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
      });

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });

    it('should include include_request parameter', async () => {
      let requestBody: any;

      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async ({ request }) => {
          requestBody = await request.json();
          return HttpResponse.json(mockDiagramResponse);
        })
      );

      await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
        include_request: true,
      });

      expect(requestBody.include_request).toBe(true);
    });

    it('should include include_response parameter', async () => {
      let requestBody: any;

      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async ({ request }) => {
          requestBody = await request.json();
          return HttpResponse.json(mockDiagramResponse);
        })
      );

      await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
        include_response: true,
      });

      expect(requestBody.include_response).toBe(true);
    });
  });

  describe('generateAuthFlowDiagram', () => {
    it('should generate bearer auth flow diagram', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.json(mockAuthFlowDiagram);
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'bearer',
      });

      expect(result.data).toEqual(mockAuthFlowDiagram);
      expect(result.error).toBeUndefined();
    });

    it('should generate oauth2 auth flow diagram', async () => {
      const oauth2Diagram = {
        ...mockAuthFlowDiagram,
        title: 'OAuth 2.0 Authentication Flow',
      };

      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.json(oauth2Diagram);
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'oauth2',
      });

      expect(result.data?.title).toBe('OAuth 2.0 Authentication Flow');
      expect(result.error).toBeUndefined();
    });

    it('should generate apikey auth flow diagram', async () => {
      const apikeyDiagram = {
        ...mockAuthFlowDiagram,
        title: 'API Key Authentication Flow',
      };

      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.json(apikeyDiagram);
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'apikey',
      });

      expect(result.data?.title).toBe('API Key Authentication Flow');
      expect(result.error).toBeUndefined();
    });

    it('should generate basic auth flow diagram', async () => {
      const basicDiagram = {
        ...mockAuthFlowDiagram,
        title: 'Basic Authentication Flow',
      };

      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.json(basicDiagram);
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'basic',
      });

      expect(result.data?.title).toBe('Basic Authentication Flow');
      expect(result.error).toBeUndefined();
    });

    it('should handle generation errors', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.json(
            { detail: 'Failed to generate auth flow diagram' },
            { status: 500 }
          );
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'bearer',
      });

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });

    it('should send correct auth_type in request', async () => {
      let requestBody: any;

      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async ({ request }) => {
          requestBody = await request.json();
          return HttpResponse.json(mockAuthFlowDiagram);
        })
      );

      await generateAuthFlowDiagram({
        auth_type: 'oauth2',
      });

      expect(requestBody.auth_type).toBe('oauth2');
    });
  });

  describe('Network Errors', () => {
    it('should handle network errors for sequence diagrams', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async () => {
          return HttpResponse.error();
        })
      );

      const result = await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
      });

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });

    it('should handle network errors for auth flow diagrams', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.error();
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'bearer',
      });

      expect(result.data).toBeUndefined();
      expect(result.error).toBeDefined();
    });
  });

  describe('Response Validation', () => {
    it('should validate sequence diagram response structure', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async () => {
          return HttpResponse.json(mockDiagramResponse);
        })
      );

      const result = await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
      });

      expect(result.data).toHaveProperty('diagram_type');
      expect(result.data).toHaveProperty('mermaid_code');
      expect(result.data).toHaveProperty('title');
    });

    it('should validate auth flow diagram response structure', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          return HttpResponse.json(mockAuthFlowDiagram);
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'bearer',
      });

      expect(result.data).toHaveProperty('diagram_type');
      expect(result.data).toHaveProperty('mermaid_code');
      expect(result.data).toHaveProperty('title');
    });
  });

  describe('Timeout Handling', () => {
    it('should handle slow sequence diagram generation', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/sequence`, async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return HttpResponse.json(mockDiagramResponse);
        })
      );

      const result = await generateSequenceDiagram({
        endpoint_id: 'test-endpoint-123',
      });

      expect(result.data).toEqual(mockDiagramResponse);
      expect(result.error).toBeUndefined();
    });

    it('should handle slow auth flow generation', async () => {
      server.use(
        http.post(`${API_URL}/diagrams/auth-flow`, async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return HttpResponse.json(mockAuthFlowDiagram);
        })
      );

      const result = await generateAuthFlowDiagram({
        auth_type: 'bearer',
      });

      expect(result.data).toEqual(mockAuthFlowDiagram);
      expect(result.error).toBeUndefined();
    });
  });
});
