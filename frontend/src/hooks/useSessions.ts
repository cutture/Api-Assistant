/**
 * React Query hooks for session management
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSession,
  getSession,
  listSessions,
  updateSession,
  deleteSession,
  getSessionStats,
  addMessageToSession,
  activateSession,
} from "@/lib/api/sessions";
import type {
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionStatus,
} from "@/types";

/**
 * Query hook for listing sessions
 */
export function useListSessions(userId?: string, status?: SessionStatus) {
  return useQuery({
    queryKey: ["sessions", { userId, status }],
    queryFn: async () => {
      const response = await listSessions(userId, status);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
  });
}

/**
 * Query hook for getting a specific session
 */
export function useSession(sessionId: string) {
  return useQuery({
    queryKey: ["session", sessionId],
    queryFn: async () => {
      const response = await getSession(sessionId);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    enabled: !!sessionId,
  });
}

/**
 * Query hook for session statistics
 */
export function useSessionStats() {
  return useQuery({
    queryKey: ["session-stats"],
    queryFn: async () => {
      const response = await getSessionStats();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

/**
 * Mutation hook for creating a session
 */
export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateSessionRequest) => {
      const response = await createSession(request);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: () => {
      // Invalidate sessions list to refetch
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({ queryKey: ["session-stats"] });
    },
  });
}

/**
 * Mutation hook for updating a session
 */
export function useUpdateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      updates,
    }: {
      sessionId: string;
      updates: UpdateSessionRequest;
    }) => {
      const response = await updateSession(sessionId, updates);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate the specific session and sessions list
      queryClient.invalidateQueries({ queryKey: ["session", variables.sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({ queryKey: ["session-stats"] });
    },
  });
}

/**
 * Mutation hook for deleting a session
 */
export function useDeleteSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await deleteSession(sessionId);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: (_, sessionId) => {
      // Remove the specific session from cache and refetch list
      queryClient.removeQueries({ queryKey: ["session", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({ queryKey: ["session-stats"] });
    },
  });
}

/**
 * Mutation hook for adding a message to a session
 */
export function useAddMessageToSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      role,
      content,
      metadata,
    }: {
      sessionId: string;
      role: "user" | "assistant" | "system";
      content: string;
      metadata?: Record<string, any>;
    }) => {
      const response = await addMessageToSession(sessionId, role, content, metadata);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate the specific session to refetch with new message
      queryClient.invalidateQueries({ queryKey: ["session", variables.sessionId] });
    },
  });
}

/**
 * Mutation hook for activating an expired or inactive session
 */
export function useActivateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      ttlMinutes,
    }: {
      sessionId: string;
      ttlMinutes?: number;
    }) => {
      const response = await activateSession(sessionId, ttlMinutes);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate the specific session, sessions list, and stats
      queryClient.invalidateQueries({ queryKey: ["session", variables.sessionId] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({ queryKey: ["session-stats"] });
    },
  });
}
