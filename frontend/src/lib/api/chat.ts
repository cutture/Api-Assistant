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
  request: ChatRequest & { files?: File[] }
): Promise<ApiResponse<ChatResponse>> {
  // The /chat endpoint ALWAYS expects multipart/form-data (not JSON)
  const formData = new FormData();
  formData.append("message", request.message);

  if (request.session_id) {
    formData.append("session_id", request.session_id);
  }

  if (request.conversation_history && request.conversation_history.length > 0) {
    formData.append("conversation_history", JSON.stringify(request.conversation_history));
  }

  formData.append("enable_url_scraping", String(request.enable_url_scraping ?? true));
  formData.append("enable_auto_indexing", String(request.enable_auto_indexing ?? true));
  formData.append("agent_type", request.agent_type || "general");

  // Append files if present
  if (request.files && request.files.length > 0) {
    request.files.forEach((file) => {
      formData.append("files", file);
    });
  }

  return apiRequest<ChatResponse>({
    method: "POST",
    url: "/chat",
    data: formData,
    // Increase timeout for file uploads (2 minutes for processing large PDFs)
    timeout: 120000,
  });
}
