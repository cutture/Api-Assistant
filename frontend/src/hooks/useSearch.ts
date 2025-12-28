/**
 * React Query hooks for search functionality
 */

"use client";

import { useMutation } from "@tanstack/react-query";
import { search, facetedSearch, quickSearch, advancedSearch } from "@/lib/api/search";
import { useSearchStore } from "@/lib/stores/searchStore";
import { SearchRequest, FacetedSearchRequest } from "@/types";

/**
 * Mutation hook for performing search
 */
export function useSearch() {
  const { setResults, setIsSearching, setSearchError, setSearchTime } =
    useSearchStore();

  return useMutation({
    mutationFn: async (request: SearchRequest) => {
      setIsSearching(true);
      setSearchError(null);

      const startTime = performance.now();
      const response = await search(request);
      const endTime = performance.now();

      if (response.error) {
        setSearchError(response.error);
        setIsSearching(false);
        throw new Error(response.error);
      }

      setResults(response.data?.results || []);
      setSearchTime(endTime - startTime);
      setIsSearching(false);

      return response.data;
    },
  });
}

/**
 * Mutation hook for faceted search
 */
export function useFacetedSearch() {
  const { setResults, setIsSearching, setSearchError, setSearchTime } =
    useSearchStore();

  return useMutation({
    mutationFn: async (request: FacetedSearchRequest) => {
      setIsSearching(true);
      setSearchError(null);

      const startTime = performance.now();
      const response = await facetedSearch(request);
      const endTime = performance.now();

      if (response.error) {
        setSearchError(response.error);
        setIsSearching(false);
        throw new Error(response.error);
      }

      setResults(response.data?.results || []);
      setSearchTime(endTime - startTime);
      setIsSearching(false);

      return response.data;
    },
  });
}

/**
 * Mutation hook for quick search
 */
export function useQuickSearch() {
  const { setResults, setIsSearching, setSearchError, setSearchTime } =
    useSearchStore();

  return useMutation({
    mutationFn: async ({
      query,
      options,
    }: {
      query: string;
      options?: { limit?: number; method?: string; source?: string };
    }) => {
      setIsSearching(true);
      setSearchError(null);

      const startTime = performance.now();
      const response = await quickSearch(query, options);
      const endTime = performance.now();

      if (response.error) {
        setSearchError(response.error);
        setIsSearching(false);
        throw new Error(response.error);
      }

      setResults(response.data?.results || []);
      setSearchTime(endTime - startTime);
      setIsSearching(false);

      return response.data;
    },
  });
}

/**
 * Mutation hook for advanced search
 */
export function useAdvancedSearch() {
  const { setResults, setIsSearching, setSearchError, setSearchTime } =
    useSearchStore();

  return useMutation({
    mutationFn: async ({
      query,
      options,
    }: {
      query: string;
      options?: { limit?: number; filters?: SearchRequest["filters"] };
    }) => {
      setIsSearching(true);
      setSearchError(null);

      const startTime = performance.now();
      const response = await advancedSearch(query, options);
      const endTime = performance.now();

      if (response.error) {
        setSearchError(response.error);
        setIsSearching(false);
        throw new Error(response.error);
      }

      setResults(response.data?.results || []);
      setSearchTime(endTime - startTime);
      setIsSearching(false);

      return response.data;
    },
  });
}
