/**
 * React Query hooks for diagram generation
 */

"use client";

import { useMutation } from "@tanstack/react-query";
import {
  generateSequenceDiagram,
  generateAuthFlowDiagram,
  generateERDiagram,
  generateOverviewDiagram,
} from "@/lib/api/diagrams";
import type {
  GenerateSequenceDiagramRequest,
  GenerateAuthFlowRequest,
  GenerateERDiagramRequest,
  GenerateOverviewRequest,
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

/**
 * Mutation hook for generating ER diagrams
 */
export function useGenerateERDiagram() {
  return useMutation({
    mutationFn: async (request: GenerateERDiagramRequest) => {
      const response = await generateERDiagram(request);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
  });
}

/**
 * Mutation hook for generating API overview diagrams
 */
export function useGenerateOverviewDiagram() {
  return useMutation({
    mutationFn: async (request: GenerateOverviewRequest) => {
      const response = await generateOverviewDiagram(request);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
  });
}
