/**
 * GitHub API client.
 */

import apiClient from './client';

export interface GitHubConnectionStatus {
  connected: boolean;
  username?: string;
  avatar_url?: string;
  scopes: string[];
  connected_at?: string;
}

export interface Repository {
  id: number;
  full_name: string;
  name: string;
  owner: string;
  description?: string;
  private: boolean;
  default_branch: string;
  language?: string;
  html_url: string;
  size: number;
  stargazers_count: number;
}

export interface RepositoryListResponse {
  repositories: Repository[];
  total: number;
  page: number;
  per_page: number;
}

export interface RepositoryContext {
  repo_full_name: string;
  default_branch: string;
  languages: Record<string, number>;
  primary_language?: string;
  framework_detected?: string;
  package_manager?: string;
  structure_summary: string;
  key_files: string[];
  patterns: string[];
  indexed_files: number;
  last_analyzed_at?: string;
}

export interface FileContent {
  path: string;
  name: string;
  content: string;
  size: number;
  language?: string;
  sha: string;
}

export interface AuthorizationUrlResponse {
  authorization_url: string;
  state: string;
}

/**
 * Initiate GitHub OAuth flow.
 * Returns the authorization URL to redirect the user to.
 */
export async function initiateGitHubOAuth(): Promise<AuthorizationUrlResponse> {
  const response = await apiClient.get<AuthorizationUrlResponse>('/github/connect');
  return response.data;
}

/**
 * Get GitHub connection status.
 */
export async function getGitHubStatus(): Promise<GitHubConnectionStatus> {
  const response = await apiClient.get<GitHubConnectionStatus>('/github/status');
  return response.data;
}

/**
 * Disconnect GitHub.
 */
export async function disconnectGitHub(): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    '/github/disconnect'
  );
  return response.data;
}

/**
 * List user's GitHub repositories.
 */
export async function listRepositories(
  page: number = 1,
  perPage: number = 30
): Promise<RepositoryListResponse> {
  const response = await apiClient.get<RepositoryListResponse>('/github/repos', {
    params: { page, per_page: perPage },
  });
  return response.data;
}

/**
 * Analyze a repository.
 */
export async function analyzeRepository(
  owner: string,
  repo: string
): Promise<RepositoryContext> {
  const response = await apiClient.post<RepositoryContext>(
    `/github/repos/${owner}/${repo}/analyze`
  );
  return response.data;
}

/**
 * Get cached repository context.
 */
export async function getRepositoryContext(
  owner: string,
  repo: string
): Promise<RepositoryContext> {
  const response = await apiClient.get<RepositoryContext>(
    `/github/repos/${owner}/${repo}/context`
  );
  return response.data;
}

/**
 * Get file content from repository.
 */
export async function getFileContent(
  owner: string,
  repo: string,
  path: string
): Promise<FileContent> {
  const response = await apiClient.get<FileContent>(
    `/github/repos/${owner}/${repo}/file`,
    { params: { path } }
  );
  return response.data;
}

/**
 * Clear repository context cache.
 */
export async function clearRepositoryContext(
  owner: string,
  repo: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    `/github/repos/${owner}/${repo}/context`
  );
  return response.data;
}

export const githubApi = {
  initiateGitHubOAuth,
  getGitHubStatus,
  disconnectGitHub,
  listRepositories,
  analyzeRepository,
  getRepositoryContext,
  getFileContent,
  clearRepositoryContext,
};

export default githubApi;
