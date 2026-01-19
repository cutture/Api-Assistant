/**
 * Artifacts API client
 *
 * Provides methods for artifact management operations.
 */

import apiClient from "./client";

// Types
export interface Artifact {
  id: string;
  name: string;
  type: "uploaded" | "generated" | "output" | "screenshot" | "preview";
  mime_type?: string;
  size_bytes?: number;
  language?: string;
  download_url: string;
  created_at: string;
  expires_at?: string;
}

export interface ArtifactListResponse {
  artifacts: Artifact[];
  total: number;
  page: number;
  limit: number;
}

export interface UploadResponse {
  artifact_id: string;
  name: string;
  type: string;
  size_bytes: number;
  chromadb_indexed: boolean;
}

export interface DeleteResponse {
  success: boolean;
  artifact_id: string;
  message: string;
}

// API functions
export async function uploadArtifact(
  file: File,
  options: {
    artifact_type?: string;
    session_id?: string;
  } = {}
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  if (options.artifact_type) {
    formData.append("artifact_type", options.artifact_type);
  }
  if (options.session_id) {
    formData.append("session_id", options.session_id);
  }

  const response = await apiClient.post<UploadResponse>(
    "/artifacts/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

export async function listArtifacts(
  options: {
    session_id?: string;
    artifact_type?: string;
    language?: string;
    page?: number;
    limit?: number;
  } = {}
): Promise<ArtifactListResponse> {
  const params = new URLSearchParams();

  if (options.session_id) params.append("session_id", options.session_id);
  if (options.artifact_type) params.append("artifact_type", options.artifact_type);
  if (options.language) params.append("language", options.language);
  if (options.page) params.append("page", options.page.toString());
  if (options.limit) params.append("limit", options.limit.toString());

  const response = await apiClient.get<ArtifactListResponse>(
    `/artifacts?${params.toString()}`
  );
  return response.data;
}

export async function getArtifact(artifactId: string): Promise<Artifact> {
  const response = await apiClient.get<Artifact>(`/artifacts/${artifactId}`);
  return response.data;
}

export async function downloadArtifact(artifactId: string): Promise<Blob> {
  const response = await apiClient.get<Blob>(
    `/artifacts/${artifactId}/download`,
    {
      responseType: "blob",
    }
  );
  return response.data;
}

export async function deleteArtifact(artifactId: string): Promise<DeleteResponse> {
  const response = await apiClient.delete<DeleteResponse>(
    `/artifacts/${artifactId}`
  );
  return response.data;
}

// Helper functions
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

export function getFileIcon(mimeType?: string, language?: string): string {
  // Return icon name based on file type
  if (language) {
    const langIcons: Record<string, string> = {
      python: "python",
      javascript: "javascript",
      typescript: "typescript",
      java: "java",
      go: "go",
      csharp: "csharp",
      rust: "rust",
    };
    return langIcons[language] || "file-code";
  }

  if (mimeType) {
    if (mimeType.startsWith("image/")) return "image";
    if (mimeType.startsWith("text/")) return "file-text";
    if (mimeType === "application/json") return "file-json";
    if (mimeType === "application/zip") return "file-archive";
    if (mimeType === "application/pdf") return "file-pdf";
  }

  return "file";
}
