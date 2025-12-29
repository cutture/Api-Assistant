/**
 * Document management API functions
 */

import apiClient, { apiRequest } from "./client";
import {
  ApiResponse,
  CollectionStats,
  Document,
  DocumentUploadResponse,
} from "@/types";

/**
 * Get collection statistics
 */
export async function getCollectionStats(): Promise<ApiResponse<CollectionStats>> {
  return apiRequest<CollectionStats>({
    method: "GET",
    url: "/stats",
  });
}

/**
 * Upload and index API specification documents
 */
export async function uploadDocuments(
  files: File[],
  format?: "openapi" | "graphql" | "postman"
): Promise<ApiResponse<DocumentUploadResponse>> {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  if (format) {
    formData.append("format", format);
  }

  try {
    const response = await apiClient.post<DocumentUploadResponse>(
      "/documents/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 60000, // 1 minute timeout for file uploads
      }
    );

    return {
      data: response.data,
      status: response.status,
    };
  } catch (error: any) {
    return {
      error: error.message || "Failed to upload documents",
      status: error.status || 500,
    };
  }
}

/**
 * Delete a document by ID
 */
export async function deleteDocument(
  documentId: string
): Promise<ApiResponse<{ message: string }>> {
  return apiRequest<{ message: string }>({
    method: "DELETE",
    url: `/documents/${documentId}`,
  });
}

/**
 * Bulk delete documents
 */
export async function bulkDeleteDocuments(
  documentIds: string[]
): Promise<ApiResponse<{ message: string; deleted_count: number }>> {
  return apiRequest<{ message: string; deleted_count: number }>({
    method: "POST",
    url: "/documents/bulk-delete",
    data: { document_ids: documentIds },
  });
}

/**
 * Clear all documents (use with caution)
 */
export async function clearAllDocuments(): Promise<ApiResponse<{ message: string }>> {
  return apiRequest<{ message: string }>({
    method: "DELETE",
    url: "/documents",
  });
}

/**
 * Export documents
 */
export async function exportDocuments(
  limit?: number
): Promise<ApiResponse<Document[]>> {
  return apiRequest<Document[]>({
    method: "GET",
    url: "/export/documents",
    params: { limit },
  });
}
