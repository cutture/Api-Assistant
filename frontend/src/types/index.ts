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
export enum SessionStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  EXPIRED = "expired",
}

export interface UserSettings {
  default_search_mode: string;
  default_n_results: number;
  use_reranking: boolean;
  use_query_expansion: boolean;
  use_diversification: boolean;
  show_scores: boolean;
  show_metadata: boolean;
  max_content_length: number;
  default_collection?: string;
  custom_metadata: Record<string, any>;
}

export interface ConversationMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Session {
  session_id: string;
  user_id?: string;
  created_at: string;
  last_accessed: string;
  expires_at?: string;
  status: SessionStatus;
  settings: UserSettings;
  conversation_history: ConversationMessage[];
  metadata: Record<string, any>;
  collection_name?: string;
}

export interface CreateSessionRequest {
  user_id?: string;
  ttl_minutes?: number;
  settings?: UserSettings;
  collection_name?: string;
}

export interface UpdateSessionRequest {
  user_id?: string;
  status?: SessionStatus;
  settings?: UserSettings;
  metadata?: Record<string, any>;
  collection_name?: string;
}

export interface SessionListResponse {
  sessions: Session[];
  total: number;
}

export interface SessionStatsResponse {
  total_sessions: number;
  active_sessions: number;
  inactive_sessions: number;
  expired_sessions: number;
  unique_users: number;
}

// Diagram Types
export enum DiagramType {
  SEQUENCE = "sequence",
  ER = "er",
  FLOWCHART = "flowchart",
  CLASS = "class",
}

export interface GenerateSequenceDiagramRequest {
  endpoint_id: string;
}

export interface GenerateAuthFlowRequest {
  auth_type: "bearer" | "oauth2" | "apikey" | "basic";
  endpoints?: string[];
}

export interface GenerateERDiagramRequest {
  schema_content: string;
  include_types?: string[];
}

export interface GenerateOverviewRequest {
  api_title: string;
  endpoints: Array<{
    path: string;
    method: string;
    summary?: string;
    description?: string;
    tags?: string[];
    operation_id?: string;
  }>;
}

export interface DiagramResponse {
  diagram_type: DiagramType;
  mermaid_code: string;
  title?: string;
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
