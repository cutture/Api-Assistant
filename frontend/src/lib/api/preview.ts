/**
 * Preview API client
 *
 * Provides methods for live preview operations.
 */

import { apiClient } from "./client";

// Types
export interface StartPreviewRequest {
  execution_id: string;
  code: string;
  language: string;
  framework?: string;
  dependencies?: string[];
  expiry_minutes?: number;
}

export interface PreviewSession {
  id: string;
  execution_id: string;
  url: string;
  port: number;
  status: "starting" | "running" | "stopped" | "error";
  created_at: string;
  expires_at: string;
  time_remaining_seconds: number;
  error_message?: string;
}

export interface PreviewStats {
  total_sessions: number;
  running: number;
  stopped: number;
  error: number;
  used_ports: number;
  available_ports: number;
}

// API functions
export async function startPreview(
  request: StartPreviewRequest
): Promise<PreviewSession> {
  const response = await apiClient.post<PreviewSession>("/preview", request);
  return response.data;
}

export async function getPreview(previewId: string): Promise<PreviewSession> {
  const response = await apiClient.get<PreviewSession>(`/preview/${previewId}`);
  return response.data;
}

export async function stopPreview(
  previewId: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    `/preview/${previewId}`
  );
  return response.data;
}

export async function listPreviews(): Promise<PreviewSession[]> {
  const response = await apiClient.get<PreviewSession[]>("/preview");
  return response.data;
}

export async function getPreviewStats(): Promise<PreviewStats> {
  const response = await apiClient.get<PreviewStats>("/preview/stats");
  return response.data;
}

export async function cleanupExpiredPreviews(): Promise<{
  success: boolean;
  cleaned_up: number;
  message: string;
}> {
  const response = await apiClient.post<{
    success: boolean;
    cleaned_up: number;
    message: string;
  }>("/preview/cleanup");
  return response.data;
}

// Polling helper for preview status
export function pollPreviewStatus(
  previewId: string,
  onUpdate: (preview: PreviewSession) => void,
  intervalMs: number = 2000
): () => void {
  let running = true;

  const poll = async () => {
    while (running) {
      try {
        const preview = await getPreview(previewId);
        onUpdate(preview);

        // Stop polling if preview is stopped or errored
        if (preview.status === "stopped" || preview.status === "error") {
          running = false;
          break;
        }
      } catch (error) {
        console.error("Error polling preview status:", error);
      }

      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
  };

  poll();

  // Return cleanup function
  return () => {
    running = false;
  };
}
