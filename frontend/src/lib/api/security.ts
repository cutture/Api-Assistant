/**
 * Security API client for vulnerability scanning.
 */

import { apiClient } from './client';

export interface Vulnerability {
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  message: string;
  line?: number;
  column?: number;
  code_snippet?: string;
  fix_suggestion?: string;
  cwe_id?: string;
  owasp_category?: string;
}

export interface ScanCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface ScanResult {
  passed: boolean;
  vulnerabilities: Vulnerability[];
  risk_score: number;
  scan_duration_ms: number;
  scanner_used: string;
  blocked: boolean;
  summary: string;
  counts: ScanCounts;
}

export interface CodeScanRequest {
  code: string;
  language: string;
  filename?: string;
}

export interface DependencyScanRequest {
  package_file: string;
  package_type: 'pip' | 'npm';
}

export interface SupportedLanguage {
  id: string;
  name: string;
  aliases: string[];
  scanners: string[];
}

export interface DependencyScanner {
  type: string;
  name: string;
  file: string;
}

export interface SupportedLanguagesResponse {
  languages: SupportedLanguage[];
  dependency_scanners: DependencyScanner[];
}

/**
 * Scan code for security vulnerabilities.
 */
export async function scanCode(request: CodeScanRequest): Promise<ScanResult> {
  const response = await apiClient.post<ScanResult>('/security/scan', request);
  return response.data;
}

/**
 * Scan dependencies for known vulnerabilities.
 */
export async function scanDependencies(
  request: DependencyScanRequest
): Promise<ScanResult> {
  const response = await apiClient.post<ScanResult>(
    '/security/scan/dependencies',
    request
  );
  return response.data;
}

/**
 * Get security scan results for a specific execution.
 */
export async function getExecutionSecurityScan(
  executionId: string
): Promise<ScanResult> {
  const response = await apiClient.get<ScanResult>(
    `/security/scan/${executionId}`
  );
  return response.data;
}

/**
 * Get list of supported languages for security scanning.
 */
export async function getSupportedLanguages(): Promise<SupportedLanguagesResponse> {
  const response = await apiClient.get<SupportedLanguagesResponse>(
    '/security/supported-languages'
  );
  return response.data;
}

export const securityApi = {
  scanCode,
  scanDependencies,
  getExecutionSecurityScan,
  getSupportedLanguages,
};

export default securityApi;
