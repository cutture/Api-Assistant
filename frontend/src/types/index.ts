/**
 * Core type definitions for the API Integration Assistant frontend
 */

// API Document Types
export interface Document {
  id: string;
  content: string;
  metadata: DocumentMetadata;
  embedding?: number[];
}

export interface DocumentMetadata {
  source: "openapi" | "graphql" | "postman";
  api_name?: string;
  endpoint?: string;
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "OPTIONS" | "HEAD";
  path?: string;
  operation_id?: string;
  tags?: string[];
  description?: string;
  summary?: string;
  file_path?: string;
  chunk_index?: number;
  total_chunks?: number;
  [key: string]: any;
}

// Search Types
export interface SearchRequest {
  query: string;
  n_results?: number;
  use_hybrid?: boolean;
  use_reranking?: boolean;
  use_query_expansion?: boolean;
  filters?: SearchFilters;
}

export interface SearchFilters {
  operator: "and" | "or" | "not";
  filters: Filter[];
}

export interface Filter {
  field: string;
  operator: "eq" | "ne" | "gt" | "gte" | "lt" | "lte" | "in" | "nin" | "contains";
  value: any;
}

export interface SearchResult {
  document: Document;
  score: number;
  rank?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  total_results: number;
  search_time_ms: number;
  metadata: {
    use_hybrid: boolean;
    use_reranking: boolean;
    use_query_expansion: boolean;
  };
}

// Faceted Search Types
export interface FacetedSearchRequest extends SearchRequest {
  facet_fields: string[];
}

export interface Facet {
  field: string;
  values: FacetValue[];
}

export interface FacetValue {
  value: any;
  count: number;
}

export interface FacetedSearchResponse extends SearchResponse {
  facets: Facet[];
}

// Collection Types
export interface CollectionStats {
  total_documents: number;
  sources: Record<string, number>;
  methods: Record<string, number>;
  apis: string[];
}

// Document Upload Types
export interface DocumentUploadRequest {
  file: File;
  format?: "openapi" | "graphql" | "postman";
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  document_count: number;
  documents?: Document[];
}

// Session Types
export interface Session {
  session_id: string;
  user_id: string;
  created_at: string;
  expires_at: string;
  conversation_history: ConversationMessage[];
}

export interface ConversationMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

// Chat Types
export interface ChatRequest {
  message: string;
  session_id?: string;
  context?: SearchResult[];
}

export interface ChatResponse {
  message: string;
  sources?: SearchResult[];
  session_id?: string;
}

// API Response Wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

// Error Types
export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: any;
}
