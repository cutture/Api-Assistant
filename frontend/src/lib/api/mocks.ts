/**
 * Mock Server API client.
 */

import { apiClient } from './client';

export interface MockEndpoint {
  method: string;
  path: string;
  response_body: any;
  status_code: number;
  headers: Record<string, string>;
  delay_ms: number;
  description?: string;
}

export interface MockServer {
  id: string;
  user_id: string;
  name: string;
  endpoints: MockEndpoint[];
  status: 'starting' | 'running' | 'stopped' | 'error';
  port?: number;
  url?: string;
  session_id?: string;
  spec_type?: string;
  created_at: string;
  expires_at?: string;
  request_count: number;
  error_message?: string;
}

export interface CreateMockRequest {
  name: string;
  endpoints: MockEndpoint[];
  session_id?: string;
  spec_url?: string;
  expiry_minutes?: number;
}

export interface UpdateMockRequest {
  name?: string;
  endpoints?: MockEndpoint[];
}

export interface RequestLog {
  mock_id: string;
  timestamp: string;
  method: string;
  path: string;
  query_params: Record<string, any>;
  response_status: number;
  response_time_ms: number;
}

export interface MockStats {
  total_mocks: number;
  running_mocks: number;
  stopped_mocks: number;
  total_requests_served: number;
  used_ports: number;
  available_ports: number;
}

export interface GenerateCrudRequest {
  resource_name: string;
  schema?: Record<string, any>;
}

export interface GenerateFromOpenApiRequest {
  spec: Record<string, any>;
}

/**
 * Create a new mock server.
 */
export async function createMock(request: CreateMockRequest): Promise<MockServer> {
  const response = await apiClient.post<MockServer>('/mocks', request);
  return response.data;
}

/**
 * List all mock servers for the current user.
 */
export async function listMocks(): Promise<MockServer[]> {
  const response = await apiClient.get<MockServer[]>('/mocks');
  return response.data;
}

/**
 * Get a specific mock server by ID.
 */
export async function getMock(mockId: string): Promise<MockServer> {
  const response = await apiClient.get<MockServer>(`/mocks/${mockId}`);
  return response.data;
}

/**
 * Update a mock server's endpoints or name.
 */
export async function updateMock(
  mockId: string,
  request: UpdateMockRequest
): Promise<MockServer> {
  const response = await apiClient.patch<MockServer>(`/mocks/${mockId}`, request);
  return response.data;
}

/**
 * Stop and delete a mock server.
 */
export async function deleteMock(
  mockId: string
): Promise<{ deleted: boolean; mock_id: string }> {
  const response = await apiClient.delete<{ deleted: boolean; mock_id: string }>(
    `/mocks/${mockId}`
  );
  return response.data;
}

/**
 * Stop a running mock server.
 */
export async function stopMock(
  mockId: string
): Promise<{ stopped: boolean; mock_id: string }> {
  const response = await apiClient.post<{ stopped: boolean; mock_id: string }>(
    `/mocks/${mockId}/stop`
  );
  return response.data;
}

/**
 * Get request logs for a mock server.
 */
export async function getMockLogs(
  mockId: string,
  limit: number = 100
): Promise<RequestLog[]> {
  const response = await apiClient.get<RequestLog[]>(
    `/mocks/${mockId}/logs`,
    { params: { limit } }
  );
  return response.data;
}

/**
 * Get mock service statistics.
 */
export async function getMockStats(): Promise<MockStats> {
  const response = await apiClient.get<MockStats>('/mocks/stats');
  return response.data;
}

/**
 * Generate CRUD endpoints for a resource.
 */
export async function generateCrudEndpoints(
  request: GenerateCrudRequest
): Promise<MockEndpoint[]> {
  const response = await apiClient.post<MockEndpoint[]>(
    '/mocks/generate/crud',
    request
  );
  return response.data;
}

/**
 * Generate endpoints from an OpenAPI specification.
 */
export async function generateFromOpenApi(
  request: GenerateFromOpenApiRequest
): Promise<MockEndpoint[]> {
  const response = await apiClient.post<MockEndpoint[]>(
    '/mocks/generate/openapi',
    request
  );
  return response.data;
}

/**
 * Clean up expired mock servers.
 */
export async function cleanupExpiredMocks(): Promise<{ cleaned_up: number }> {
  const response = await apiClient.post<{ cleaned_up: number }>('/mocks/cleanup');
  return response.data;
}

export const mocksApi = {
  createMock,
  listMocks,
  getMock,
  updateMock,
  deleteMock,
  stopMock,
  getMockLogs,
  getMockStats,
  generateCrudEndpoints,
  generateFromOpenApi,
  cleanupExpiredMocks,
};

export default mocksApi;
