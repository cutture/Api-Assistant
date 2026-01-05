/**
 * Settings store using Zustand
 * Manages application-wide settings with localStorage persistence
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AppSettings {
  // LLM Provider Settings
  llmProvider: "ollama" | "groq";
  ollamaBaseUrl: string;
  groqApiKey: string;

  // Search Defaults
  defaultSearchMode: "vector" | "hybrid" | "reranked";
  useReranking: boolean;
  useQueryExpansion: boolean;
  useDiversification: boolean;
  defaultNResults: number;

  // UI Preferences
  theme: "light" | "dark" | "system";
  showScores: boolean;
  showMetadata: boolean;
  maxContentLength: number;

  // Session Defaults
  defaultSessionTtl: number; // minutes
  enableAutoCleanup: boolean;
}

interface SettingsStore {
  settings: AppSettings;
  updateSettings: (updates: Partial<AppSettings>) => void;
  resetSettings: () => void;
}

const defaultSettings: AppSettings = {
  // LLM Provider
  llmProvider: "ollama",
  ollamaBaseUrl: "http://localhost:11434",
  groqApiKey: "",

  // Search
  defaultSearchMode: "hybrid",
  useReranking: true,
  useQueryExpansion: true,
  useDiversification: false,
  defaultNResults: 10,

  // UI
  theme: "system",
  showScores: true,
  showMetadata: true,
  maxContentLength: 500,

  // Session
  defaultSessionTtl: 60,
  enableAutoCleanup: true,
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      updateSettings: (updates) =>
        set((state) => ({
          settings: { ...state.settings, ...updates },
        })),
      resetSettings: () =>
        set({
          settings: defaultSettings,
        }),
    }),
    {
      name: "api-assistant-settings",
    }
  )
);
