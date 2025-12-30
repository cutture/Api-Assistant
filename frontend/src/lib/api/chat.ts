/**
 * Chat API functions
 */

import { apiRequest } from "./client";
import type { ApiResponse } from "@/types";

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
}

export interface ChatSource {
  type: string;
  title: string;
  url?: string;
  api_name?: string;
  method?: string;
  score: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  conversation_history?: ChatMessage[];
  enable_url_scraping?: boolean;
  enable_auto_indexing?: boolean;
  agent_type?: "general" | "code" | "reasoning";
}

export interface ChatResponse {
  response: string;
  sources: ChatSource[];
  scraped_urls: string[];
  indexed_docs: number;
  context_results: number;
  session_id?: string;
  timestamp: string;
}

/**
 * Send a chat message and get AI-generated response
 */
export async function sendChatMessage(
  request: ChatRequest
): Promise<ApiResponse<ChatResponse>> {
  return apiRequest<ChatResponse>({
    method: "POST",
    url: "/chat",
    data: {
      message: request.message,
      session_id: request.session_id,
      conversation_history: request.conversation_history || [],
      enable_url_scraping: request.enable_url_scraping ?? true,
      enable_auto_indexing: request.enable_auto_indexing ?? true,
      agent_type: request.agent_type || "general",
    },
  });
}
