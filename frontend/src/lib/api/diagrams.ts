/**
 * Diagram generation API functions
 */

import { apiRequest } from "./client";
import type {
  ApiResponse,
  DiagramResponse,
  GenerateSequenceDiagramRequest,
  GenerateAuthFlowRequest,
} from "@/types";

/**
 * Generate a sequence diagram from an API endpoint
 */
export async function generateSequenceDiagram(
  request: GenerateSequenceDiagramRequest
): Promise<ApiResponse<DiagramResponse>> {
  return apiRequest<DiagramResponse>({
    method: "POST",
    url: "/diagrams/sequence",
    data: request,
  });
}

/**
 * Generate an authentication flow diagram
 */
export async function generateAuthFlowDiagram(
  request: GenerateAuthFlowRequest
): Promise<ApiResponse<DiagramResponse>> {
  return apiRequest<DiagramResponse>({
    method: "POST",
    url: "/diagrams/auth-flow",
    data: request,
  });
}
