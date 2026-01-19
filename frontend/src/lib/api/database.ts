/**
 * Database API client.
 */

import { apiClient } from './client';

export type DatabaseType = 'postgresql' | 'mysql' | 'sqlite' | 'mongodb';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  risk_level: RiskLevel;
  query_type: string | null;
  affected_tables: string[];
  has_where_clause: boolean;
  is_parameterized: boolean;
}

export interface QueryExplanation {
  summary: string;
  query_type: string;
  database_type: string;
  tables_involved: string[];
  columns_involved: string[];
  conditions: string[];
  operations: string[];
  performance_hints: string[];
  security_notes: string[];
}

export interface GeneratedQuery {
  query: string;
  database_type: string;
  query_type: string;
  parameters: Record<string, any>;
  validation: ValidationResult | null;
  explanation: QueryExplanation | null;
}

export interface DatabaseInfo {
  id: string;
  name: string;
  features: string[];
  parameterization: string;
}

export interface ColumnDefinition {
  type: string;
  primary_key?: boolean;
  nullable?: boolean;
  unique?: boolean;
  default?: any;
}

/**
 * Validate a database query.
 */
export async function validateQuery(
  query: string,
  databaseType: DatabaseType = 'postgresql'
): Promise<ValidationResult> {
  const response = await apiClient.post<ValidationResult>('/database/validate', {
    query,
    database_type: databaseType,
  });
  return response.data;
}

/**
 * Explain what a query does.
 */
export async function explainQuery(
  query: string,
  databaseType: DatabaseType = 'postgresql'
): Promise<QueryExplanation> {
  const response = await apiClient.post<QueryExplanation>('/database/explain', {
    query,
    database_type: databaseType,
  });
  return response.data;
}

/**
 * Generate a SELECT query.
 */
export async function generateSelect(options: {
  table: string;
  columns?: string[];
  conditions?: Record<string, any>;
  order_by?: string;
  order_direction?: 'ASC' | 'DESC';
  limit?: number;
  offset?: number;
  database_type?: DatabaseType;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>('/database/generate/select', {
    ...options,
    database_type: options.database_type || 'postgresql',
  });
  return response.data;
}

/**
 * Generate an INSERT query.
 */
export async function generateInsert(options: {
  table: string;
  data: Record<string, any>;
  database_type?: DatabaseType;
  returning?: string;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>('/database/generate/insert', {
    ...options,
    database_type: options.database_type || 'postgresql',
  });
  return response.data;
}

/**
 * Generate an UPDATE query.
 */
export async function generateUpdate(options: {
  table: string;
  data: Record<string, any>;
  conditions: Record<string, any>;
  database_type?: DatabaseType;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>('/database/generate/update', {
    ...options,
    database_type: options.database_type || 'postgresql',
  });
  return response.data;
}

/**
 * Generate a DELETE query.
 */
export async function generateDelete(options: {
  table: string;
  conditions: Record<string, any>;
  database_type?: DatabaseType;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>('/database/generate/delete', {
    ...options,
    database_type: options.database_type || 'postgresql',
  });
  return response.data;
}

/**
 * Generate a CREATE TABLE query.
 */
export async function generateCreateTable(options: {
  table: string;
  columns: Record<string, ColumnDefinition>;
  database_type?: DatabaseType;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>('/database/generate/create-table', {
    ...options,
    database_type: options.database_type || 'postgresql',
  });
  return response.data;
}

/**
 * Generate a MongoDB find query.
 */
export async function generateMongoFind(options: {
  collection: string;
  filter_query?: Record<string, any>;
  projection?: Record<string, any>;
  sort?: Record<string, any>;
  limit?: number;
  skip?: number;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>(
    '/database/generate/mongodb/find',
    options
  );
  return response.data;
}

/**
 * Generate a MongoDB aggregation pipeline.
 */
export async function generateMongoAggregate(options: {
  collection: string;
  pipeline: Record<string, any>[];
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>(
    '/database/generate/mongodb/aggregate',
    options
  );
  return response.data;
}

/**
 * Convert natural language to query.
 */
export async function naturalLanguageToQuery(options: {
  description: string;
  table_schema?: Record<string, any>;
  database_type?: DatabaseType;
}): Promise<GeneratedQuery> {
  const response = await apiClient.post<GeneratedQuery>(
    '/database/generate/natural-language',
    {
      ...options,
      database_type: options.database_type || 'postgresql',
    }
  );
  return response.data;
}

/**
 * Get supported database types and features.
 */
export async function getSupportedTypes(): Promise<{
  databases: DatabaseInfo[];
  column_types: string[];
}> {
  const response = await apiClient.get<{
    databases: DatabaseInfo[];
    column_types: string[];
  }>('/database/types');
  return response.data;
}

/**
 * Get risk level information.
 */
export async function getRiskLevels(): Promise<{
  levels: Array<{
    level: RiskLevel;
    description: string;
    color: string;
  }>;
  dangerous_patterns: string[];
}> {
  const response = await apiClient.get<{
    levels: Array<{
      level: RiskLevel;
      description: string;
      color: string;
    }>;
    dangerous_patterns: string[];
  }>('/database/risk-levels');
  return response.data;
}

export const databaseApi = {
  validateQuery,
  explainQuery,
  generateSelect,
  generateInsert,
  generateUpdate,
  generateDelete,
  generateCreateTable,
  generateMongoFind,
  generateMongoAggregate,
  naturalLanguageToQuery,
  getSupportedTypes,
  getRiskLevels,
};

export default databaseApi;
