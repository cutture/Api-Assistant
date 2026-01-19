/**
 * Sandbox API client
 *
 * Provides methods for screenshot and UI testing operations.
 */

import { apiClient } from "./client";

// Types
export interface Viewport {
  width: number;
  height: number;
}

export interface ScreenshotRequest {
  url: string;
  viewport?: Viewport;
  full_page?: boolean;
  wait_for_selector?: string;
  wait_timeout_ms?: number;
  save_artifact?: boolean;
}

export interface ScreenshotResponse {
  width: number;
  height: number;
  url: string;
  timestamp: string;
  image_base64: string;
  artifact_id?: string;
}

export interface UITestRequest {
  url: string;
  test_script?: string;
  viewport?: Viewport;
}

export interface UITestResponse {
  passed: boolean;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  screenshots: ScreenshotResponse[];
  errors: string[];
  duration_ms: number;
}

// API functions
export async function takeScreenshot(
  request: ScreenshotRequest
): Promise<ScreenshotResponse> {
  const response = await apiClient.post<ScreenshotResponse>(
    "/sandbox/screenshot",
    request
  );
  return response.data;
}

export async function runUITests(
  request: UITestRequest
): Promise<UITestResponse> {
  const response = await apiClient.post<UITestResponse>(
    "/sandbox/test-ui",
    request
  );
  return response.data;
}

// Helper functions
export function base64ToDataUrl(base64: string): string {
  return `data:image/png;base64,${base64}`;
}

export function downloadScreenshot(
  response: ScreenshotResponse,
  filename?: string
): void {
  const link = document.createElement("a");
  link.href = base64ToDataUrl(response.image_base64);
  link.download = filename || `screenshot_${response.timestamp}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
