/**
 * React Query hooks for diagram generation
 */

"use client";

import { useMutation } from "@tanstack/react-query";
import {
  generateSequenceDiagram,
  generateAuthFlowDiagram,
} from "@/lib/api/diagrams";
import type {
  GenerateSequenceDiagramRequest,
  GenerateAuthFlowRequest,
} from "@/types";

/**
 * Mutation hook for generating sequence diagrams
 */
export function useGenerateSequenceDiagram() {
  return useMutation({
    mutationFn: async (request: GenerateSequenceDiagramRequest) => {
      const response = await generateSequenceDiagram(request);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
  });
}

/**
 * Mutation hook for generating auth flow diagrams
 */
export function useGenerateAuthFlowDiagram() {
  return useMutation({
    mutationFn: async (request: GenerateAuthFlowRequest) => {
      const response = await generateAuthFlowDiagram(request);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
  });
}
