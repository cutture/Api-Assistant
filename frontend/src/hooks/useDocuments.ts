/**
 * React Query hooks for document management
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getCollectionStats,
  uploadDocuments,
  deleteDocument,
  bulkDeleteDocuments,
  clearAllDocuments,
} from "@/lib/api/documents";
import { useDocumentStore } from "@/lib/stores/documentStore";

/**
 * Query hook for collection statistics
 */
export function useCollectionStats() {
  const { setStats, setIsLoadingStats, setStatsError } = useDocumentStore();

  return useQuery({
    queryKey: ["collection-stats"],
    queryFn: async () => {
      setIsLoadingStats(true);
      setStatsError(null);

      const response = await getCollectionStats();

      if (response.error) {
        setStatsError(response.error);
        throw new Error(response.error);
      }

      setStats(response.data || null);
      setIsLoadingStats(false);

      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

/**
 * Mutation hook for uploading documents
 */
export function useUploadDocuments() {
  const queryClient = useQueryClient();
  const { setIsUploading, setUploadProgress, setUploadError } = useDocumentStore();

  return useMutation({
    mutationFn: async ({
      files,
      format,
    }: {
      files: File[];
      format?: "openapi" | "graphql" | "postman";
    }) => {
      setIsUploading(true);
      setUploadProgress(0);
      setUploadError(null);

      try {
        const response = await uploadDocuments(files, format);

        if (response.error) {
          setUploadError(response.error);
          throw new Error(response.error);
        }

        setUploadProgress(100);
        setIsUploading(false);

        return response.data;
      } catch (error: any) {
        setUploadError(error.message || "Upload failed");
        setIsUploading(false);
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate and refetch collection stats
      queryClient.invalidateQueries({ queryKey: ["collection-stats"] });
    },
  });
}

/**
 * Mutation hook for deleting a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const response = await deleteDocument(documentId);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collection-stats"] });
    },
  });
}

/**
 * Mutation hook for bulk deleting documents
 */
export function useBulkDeleteDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentIds: string[]) => {
      const response = await bulkDeleteDocuments(documentIds);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collection-stats"] });
    },
  });
}

/**
 * Mutation hook for clearing all documents
 */
export function useClearAllDocuments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await clearAllDocuments();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collection-stats"] });
    },
  });
}
