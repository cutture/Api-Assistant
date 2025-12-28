/**
 * Search state management with Zustand
 */

import { create } from "zustand";
import { SearchRequest, SearchResult } from "@/types";

interface SearchState {
  // Search configuration
  query: string;
  useHybrid: boolean;
  useReranking: boolean;
  useQueryExpansion: boolean;
  resultsLimit: number;

  // Search results
  results: SearchResult[];
  isSearching: boolean;
  searchError: string | null;
  searchTime: number;

  // Actions
  setQuery: (query: string) => void;
  setUseHybrid: (use: boolean) => void;
  setUseReranking: (use: boolean) => void;
  setUseQueryExpansion: (use: boolean) => void;
  setResultsLimit: (limit: number) => void;
  setResults: (results: SearchResult[]) => void;
  setIsSearching: (isSearching: boolean) => void;
  setSearchError: (error: string | null) => void;
  setSearchTime: (time: number) => void;
  reset: () => void;
}

const initialState = {
  query: "",
  useHybrid: false,
  useReranking: false,
  useQueryExpansion: false,
  resultsLimit: 10,
  results: [],
  isSearching: false,
  searchError: null,
  searchTime: 0,
};

export const useSearchStore = create<SearchState>((set) => ({
  ...initialState,

  setQuery: (query) => set({ query }),
  setUseHybrid: (useHybrid) => set({ useHybrid }),
  setUseReranking: (useReranking) => set({ useReranking }),
  setUseQueryExpansion: (useQueryExpansion) => set({ useQueryExpansion }),
  setResultsLimit: (resultsLimit) => set({ resultsLimit }),
  setResults: (results) => set({ results }),
  setIsSearching: (isSearching) => set({ isSearching }),
  setSearchError: (searchError) => set({ searchError }),
  setSearchTime: (searchTime) => set({ searchTime }),
  reset: () => set(initialState),
}));
