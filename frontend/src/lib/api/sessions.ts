/**
 * Session management API functions
 */

import { apiRequest } from "./client";
import type {
  ApiResponse,
  Session,
  CreateSessionRequest,
  CreateSessionResponse,
  UpdateSessionRequest,
  SessionListResponse,
  SessionStatsResponse,
  SessionStatus,
} from "@/types";

/**
 * Create a new session
 */
export async function createSession(
  request: CreateSessionRequest
): Promise<ApiResponse<CreateSessionResponse>> {
  return apiRequest<CreateSessionResponse>({
    method: "POST",
    url: "/sessions",
    data: request,
  });
}

/**
 * Get session by ID
 */
export async function getSession(
  sessionId: string
): Promise<ApiResponse<Session>> {
  return apiRequest<Session>({
    method: "GET",
    url: `/sessions/${sessionId}`,
  });
}

/**
 * List all sessions with optional filters
 */
export async function listSessions(
  userId?: string,
  status?: SessionStatus
): Promise<ApiResponse<SessionListResponse>> {
  const params = new URLSearchParams();
  if (userId) params.append("user_id", userId);
  if (status) params.append("status_filter", status);

  return apiRequest<SessionListResponse>({
    method: "GET",
    url: `/sessions${params.toString() ? `?${params.toString()}` : ""}`,
  });
}

/**
 * Update session attributes
 */
export async function updateSession(
  sessionId: string,
  updates: UpdateSessionRequest
): Promise<ApiResponse<Session>> {
  return apiRequest<Session>({
    method: "PATCH",
    url: `/sessions/${sessionId}`,
    data: updates,
  });
}

/**
 * Delete a session
 */
export async function deleteSession(
  sessionId: string
): Promise<ApiResponse<{ success: boolean; message: string }>> {
  return apiRequest<{ success: boolean; message: string }>({
    method: "DELETE",
    url: `/sessions/${sessionId}`,
  });
}

/**
 * Get session statistics
 */
export async function getSessionStats(): Promise<
  ApiResponse<SessionStatsResponse>
> {
  return apiRequest<SessionStatsResponse>({
    method: "GET",
    url: "/sessions/stats",
  });
}

/**
 * Add a message to session conversation history
 */
export async function addMessageToSession(
  sessionId: string,
  role: "user" | "assistant" | "system",
  content: string,
  metadata?: Record<string, any>
): Promise<ApiResponse<Session>> {
  return apiRequest<Session>({
    method: "POST",
    url: `/sessions/${sessionId}/messages`,
    data: {
      role,
      content,
      metadata,
    },
  });
}

/**
 * Get session conversation history
 */
export async function getSessionHistory(
  sessionId: string
): Promise<ApiResponse<Session>> {
  return apiRequest<Session>({
    method: "GET",
    url: `/sessions/${sessionId}`,
  });
}

/**
 * Activate an expired or inactive session
 */
export async function activateSession(
  sessionId: string,
  ttlMinutes?: number
): Promise<ApiResponse<Session>> {
  return apiRequest<Session>({
    method: "POST",
    url: `/sessions/${sessionId}/activate`,
    params: ttlMinutes ? { ttl_minutes: ttlMinutes } : undefined,
  });
}
