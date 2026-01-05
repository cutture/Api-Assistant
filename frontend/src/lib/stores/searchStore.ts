/**
 * Search state management with Zustand
 */

import { create } from "zustand";
import { SearchRequest, SearchResult, SearchMode } from "@/types";

interface SearchState {
  // Search configuration
  query: string;
  mode: SearchMode;
  useQueryExpansion: boolean;
  resultsLimit: number;
  minScore: number; // Minimum relevance score threshold

  // Search results
  results: SearchResult[];
  isSearching: boolean;
  searchError: string | null;
  searchTime: number;

  // Pagination
  currentPage: number;
  totalResults: number;

  // Actions
  setQuery: (query: string) => void;
  setMode: (mode: SearchMode) => void;
  setUseQueryExpansion: (use: boolean) => void;
  setResultsLimit: (limit: number) => void;
  setMinScore: (score: number) => void;
  setResults: (results: SearchResult[]) => void;
  setIsSearching: (isSearching: boolean) => void;
  setSearchError: (error: string | null) => void;
  setSearchTime: (time: number) => void;
  setCurrentPage: (page: number) => void;
  setTotalResults: (total: number) => void;
  reset: () => void;
}

const initialState = {
  query: "",
  mode: "hybrid" as SearchMode,
  useQueryExpansion: false,
  resultsLimit: 10,
  minScore: 0.0, // Default: no filtering
  results: [],
  isSearching: false,
  searchError: null,
  searchTime: 0,
  currentPage: 1,
  totalResults: 0,
};

export const useSearchStore = create<SearchState>((set) => ({
  ...initialState,

  setQuery: (query) => set({ query, currentPage: 1 }), // Reset to page 1 on new query
  setMode: (mode) => set({ mode }),
  setUseQueryExpansion: (useQueryExpansion) => set({ useQueryExpansion }),
  setResultsLimit: (resultsLimit) => set({ resultsLimit, currentPage: 1 }), // Reset to page 1 on limit change
  setMinScore: (minScore) => set({ minScore }),
  setResults: (results) => set({ results, totalResults: results.length }),
  setIsSearching: (isSearching) => set({ isSearching }),
  setSearchError: (searchError) => set({ searchError }),
  setSearchTime: (searchTime) => set({ searchTime }),
  setCurrentPage: (currentPage) => set({ currentPage }),
  setTotalResults: (totalResults) => set({ totalResults }),
  reset: () => set(initialState),
}));
