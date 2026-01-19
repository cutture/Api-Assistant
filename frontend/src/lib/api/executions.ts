/**
 * Executions API client
 *
 * Provides methods for code execution operations.
 */

import { apiClient } from "./client";

// Types
export interface ExecuteRequest {
  prompt: string;
  language?: string;
  session_id?: string;
  context_artifacts?: string[];
  llm_preference?: "fast" | "balanced" | "quality";
  output_preference?: "snippet" | "zip" | "pr";
  skip_tests?: boolean;
}

export interface ExecuteResponse {
  execution_id: string;
  status: string;
  estimated_time_seconds: number;
}

export interface ExecutionStatus {
  id: string;
  status: "pending" | "running" | "passed" | "failed" | "partial";
  attempt: number;
  language: string;
  complexity_score?: number;
  llm_provider?: string;
  llm_model?: string;
  code?: string;
  tests?: string;
  test_passed?: boolean;
  lint_passed?: boolean;
  security_passed?: boolean;
  stdout?: string;
  stderr?: string;
  quality_score?: number;
  output_type?: string;
  output_artifact_id?: string;
  created_at: string;
  completed_at?: string;
}

export interface ExecutionDiff {
  from_attempt: number;
  to_attempt: number;
  unified_diff: string;
  changes_summary: string;
}

export interface ExecutionListItem {
  id: string;
  prompt: string;
  language: string;
  status: string;
  attempt_number: number;
  quality_score?: number;
  created_at: string;
}

export interface ExecutionListResponse {
  executions: ExecutionListItem[];
  total: number;
  page: number;
  limit: number;
}

// API functions
export async function executeCode(request: ExecuteRequest): Promise<ExecuteResponse> {
  const response = await apiClient.post<ExecuteResponse>("/execute", request);
  return response.data;
}

export async function getExecutionStatus(executionId: string): Promise<ExecutionStatus> {
  const response = await apiClient.get<ExecutionStatus>(`/execute/${executionId}`);
  return response.data;
}

export async function getExecutionDiff(
  executionId: string,
  fromAttempt: number = 1,
  toAttempt?: number
): Promise<ExecutionDiff> {
  const params = new URLSearchParams();
  params.append("from_attempt", fromAttempt.toString());
  if (toAttempt !== undefined) {
    params.append("to_attempt", toAttempt.toString());
  }

  const response = await apiClient.get<ExecutionDiff>(
    `/execute/${executionId}/diff?${params.toString()}`
  );
  return response.data;
}

export async function retryExecution(
  executionId: string,
  customPrompt?: string
): Promise<ExecuteResponse> {
  const response = await apiClient.post<ExecuteResponse>(
    `/execute/${executionId}/retry`,
    { custom_prompt: customPrompt }
  );
  return response.data;
}

export async function listExecutions(
  options: {
    session_id?: string;
    status?: string;
    language?: string;
    page?: number;
    limit?: number;
  } = {}
): Promise<ExecutionListResponse> {
  const params = new URLSearchParams();

  if (options.session_id) params.append("session_id", options.session_id);
  if (options.status) params.append("status", options.status);
  if (options.language) params.append("language", options.language);
  if (options.page) params.append("page", options.page.toString());
  if (options.limit) params.append("limit", options.limit.toString());

  const response = await apiClient.get<ExecutionListResponse>(
    `/executes?${params.toString()}`
  );
  return response.data;
}

// Polling helper for execution status
export function pollExecutionStatus(
  executionId: string,
  onUpdate: (status: ExecutionStatus) => void,
  options: {
    intervalMs?: number;
    maxAttempts?: number;
  } = {}
): () => void {
  const { intervalMs = 2000, maxAttempts = 60 } = options;
  let attempts = 0;
  let stopped = false;

  const poll = async () => {
    if (stopped) return;

    try {
      const status = await getExecutionStatus(executionId);
      onUpdate(status);

      // Stop polling if execution is complete
      if (["passed", "failed", "partial"].includes(status.status)) {
        return;
      }

      // Continue polling
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(poll, intervalMs);
      }
    } catch (error) {
      console.error("Failed to poll execution status:", error);
      // Retry after error
      if (attempts < maxAttempts) {
        setTimeout(poll, intervalMs * 2);
      }
    }
  };

  // Start polling
  poll();

  // Return stop function
  return () => {
    stopped = true;
  };
}
