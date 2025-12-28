/**
 * Document state management with Zustand
 */

import { create } from "zustand";
import { CollectionStats } from "@/types";

interface DocumentState {
  // Collection stats
  stats: CollectionStats | null;
  isLoadingStats: boolean;
  statsError: string | null;

  // Upload state
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;

  // Actions
  setStats: (stats: CollectionStats | null) => void;
  setIsLoadingStats: (isLoading: boolean) => void;
  setStatsError: (error: string | null) => void;
  setIsUploading: (isUploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setUploadError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  stats: null,
  isLoadingStats: false,
  statsError: null,
  isUploading: false,
  uploadProgress: 0,
  uploadError: null,
};

export const useDocumentStore = create<DocumentState>((set) => ({
  ...initialState,

  setStats: (stats) => set({ stats }),
  setIsLoadingStats: (isLoadingStats) => set({ isLoadingStats }),
  setStatsError: (statsError) => set({ statsError }),
  setIsUploading: (isUploading) => set({ isUploading }),
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),
  setUploadError: (uploadError) => set({ uploadError }),
  reset: () => set(initialState),
}));
