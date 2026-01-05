/**
 * Health check API functions
 */

import { apiRequest } from "./client";
import { ApiResponse } from "@/types";

export interface HealthResponse {
  status: "healthy" | "unhealthy";
  timestamp?: string;
}

/**
 * Check backend health
 */
export async function checkHealth(): Promise<ApiResponse<HealthResponse>> {
  return apiRequest<HealthResponse>({
    method: "GET",
    url: "/health",
  });
}
