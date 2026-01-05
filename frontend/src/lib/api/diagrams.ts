/**
 * Diagram generation API functions
 */

import { apiRequest } from "./client";
import type {
  ApiResponse,
  DiagramResponse,
  GenerateSequenceDiagramRequest,
  GenerateAuthFlowRequest,
  GenerateERDiagramRequest,
  GenerateOverviewRequest,
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

/**
 * Generate an Entity-Relationship diagram from GraphQL schema
 */
export async function generateERDiagram(
  request: GenerateERDiagramRequest
): Promise<ApiResponse<DiagramResponse>> {
  return apiRequest<DiagramResponse>({
    method: "POST",
    url: "/diagrams/er",
    data: request,
  });
}

/**
 * Generate an API overview diagram
 */
export async function generateOverviewDiagram(
  request: GenerateOverviewRequest
): Promise<ApiResponse<DiagramResponse>> {
  return apiRequest<DiagramResponse>({
    method: "POST",
    url: "/diagrams/overview",
    data: request,
  });
}
