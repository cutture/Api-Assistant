/**
 * Templates API client.
 */

import apiClient from './client';

export interface TemplateParameter {
  name: string;
  description: string;
  type: string;
  required: boolean;
  default?: any;
  enum_values?: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  language: string;
  template_code: string;
  test_template?: string;
  parameters: TemplateParameter[];
  tags: string[];
  usage_count: number;
  is_builtin: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface TemplateListItem {
  id: string;
  name: string;
  description: string;
  category: string;
  language: string;
  tags: string[];
  usage_count: number;
  is_builtin: boolean;
}

export interface CreateTemplateRequest {
  name: string;
  description: string;
  category: string;
  language: string;
  template_code: string;
  test_template?: string;
  parameters?: Array<{
    name: string;
    description?: string;
    type?: string;
    required?: boolean;
    default?: any;
    enum_values?: string[];
  }>;
  tags?: string[];
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  template_code?: string;
  test_template?: string;
  tags?: string[];
}

export interface RenderTemplateResponse {
  code: string;
  tests?: string;
  template_id: string;
  template_name: string;
}

export interface Category {
  id: string;
  name: string;
  count: number;
}

export interface Language {
  id: string;
  name: string;
  count: number;
}

/**
 * List available templates with optional filtering.
 */
export async function listTemplates(options?: {
  category?: string;
  language?: string;
  tags?: string[];
}): Promise<TemplateListItem[]> {
  const params = new URLSearchParams();
  if (options?.category) params.set('category', options.category);
  if (options?.language) params.set('language', options.language);
  if (options?.tags?.length) params.set('tags', options.tags.join(','));

  const url = params.toString() ? `/templates?${params}` : '/templates';
  const response = await apiClient.get<TemplateListItem[]>(url);
  return response.data;
}

/**
 * Get a template by ID.
 */
export async function getTemplate(templateId: string): Promise<Template> {
  const response = await apiClient.get<Template>(`/templates/${templateId}`);
  return response.data;
}

/**
 * Get list of template categories.
 */
export async function getCategories(): Promise<Category[]> {
  const response = await apiClient.get<Category[]>('/templates/categories');
  return response.data;
}

/**
 * Get list of supported languages.
 */
export async function getLanguages(): Promise<Language[]> {
  const response = await apiClient.get<Language[]>('/templates/languages');
  return response.data;
}

/**
 * Create a new custom template.
 */
export async function createTemplate(
  request: CreateTemplateRequest
): Promise<Template> {
  const response = await apiClient.post<Template>('/templates', request);
  return response.data;
}

/**
 * Update a custom template.
 */
export async function updateTemplate(
  templateId: string,
  request: UpdateTemplateRequest
): Promise<Template> {
  const response = await apiClient.patch<Template>(
    `/templates/${templateId}`,
    request
  );
  return response.data;
}

/**
 * Delete a custom template.
 */
export async function deleteTemplate(
  templateId: string
): Promise<{ deleted: boolean; template_id: string }> {
  const response = await apiClient.delete<{ deleted: boolean; template_id: string }>(
    `/templates/${templateId}`
  );
  return response.data;
}

/**
 * Render a template with parameters.
 */
export async function renderTemplate(
  templateId: string,
  parameters: Record<string, any>
): Promise<RenderTemplateResponse> {
  const response = await apiClient.post<RenderTemplateResponse>(
    `/templates/${templateId}/render`,
    { parameters }
  );
  return response.data;
}

export const templatesApi = {
  listTemplates,
  getTemplate,
  getCategories,
  getLanguages,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  renderTemplate,
};

export default templatesApi;
