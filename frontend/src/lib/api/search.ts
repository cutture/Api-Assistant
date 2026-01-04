/**
 * Search API functions
 */

import { apiRequest } from "./client";
import {
  ApiResponse,
  SearchRequest,
  SearchResponse,
  FacetedSearchRequest,
  FacetedSearchResponse,
} from "@/types";

/**
 * Perform advanced search with optional hybrid mode, reranking, and query expansion
 */
export async function search(
  request: SearchRequest
): Promise<ApiResponse<SearchResponse>> {
  return apiRequest<SearchResponse>({
    method: "POST",
    url: "/search",
    data: {
      query: request.query,
      n_results: request.n_results || 5,
      mode: request.mode || "hybrid",
      filter: request.filter,
      use_query_expansion: request.use_query_expansion ?? false,
      use_diversification: request.use_diversification ?? false,
      diversification_lambda: request.diversification_lambda ?? 0.5,
      min_score: request.min_score ?? 0.0,
    },
  });
}

/**
 * Perform faceted search with aggregations
 */
export async function facetedSearch(
  request: FacetedSearchRequest
): Promise<ApiResponse<FacetedSearchResponse>> {
  return apiRequest<FacetedSearchResponse>({
    method: "POST",
    url: "/search/faceted",
    data: {
      query: request.query,
      n_results: request.n_results || 5,
      facet_fields: request.facet_fields,
      filter: request.filter,
    },
  });
}

/**
 * Quick search helper with sensible defaults
 */
export async function quickSearch(
  query: string,
  options?: {
    limit?: number;
    method?: string;
    source?: string;
  }
): Promise<ApiResponse<SearchResponse>> {
  const request: SearchRequest = {
    query,
    n_results: options?.limit || 10,
    mode: "vector",
  };

  // Add simple filters if provided
  if (options?.method || options?.source) {
    const filters: any[] = [];

    if (options.method) {
      filters.push({
        field: "method",
        operator: "eq",
        value: options.method,
      });
    }

    if (options.source) {
      filters.push({
        field: "source",
        operator: "eq",
        value: options.source,
      });
    }

    if (filters.length > 0) {
      request.filter = {
        operator: "and",
        filters,
      };
    }
  }

  return search(request);
}

/**
 * Advanced search with all features enabled
 */
export async function advancedSearch(
  query: string,
  options?: {
    limit?: number;
    filter?: SearchRequest["filter"];
  }
): Promise<ApiResponse<SearchResponse>> {
  return search({
    query,
    n_results: options?.limit || 10,
    mode: "reranked",
    use_query_expansion: true,
    filter: options?.filter,
  });
}
