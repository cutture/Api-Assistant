/**
 * Chat page - AI-powered chat interface with URL scraping and dynamic indexing
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { useToast } from "@/hooks/use-toast";
import { sendChatMessage, ChatMessage } from "@/lib/api/chat";
import { useState, useEffect, useRef } from "react";
import { useCreateSession } from "@/hooks/useSessions";

export default function ChatPage() {
  const { toast } = useToast();
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const { mutate: createSession } = useCreateSession();
  const sessionInitialized = useRef(false);

  // Create or restore session on mount
  useEffect(() => {
    // Prevent double initialization in Strict Mode or re-renders
    if (sessionInitialized.current) {
      return;
    }

    // Mark as initialized IMMEDIATELY to prevent double calls
    sessionInitialized.current = true;

    // Try to restore existing session from localStorage
    const storedSessionId = localStorage.getItem("chat_session_id");

    if (storedSessionId) {
      // Use existing session
      console.log("Restoring session:", storedSessionId);
      setSessionId(storedSessionId);
    } else {
      // Create new session only once
      console.log("Creating new session...");
      createSession(
        {
          ttl_minutes: 1440, // 24 hours
          settings: {
            default_search_mode: "hybrid",
            default_n_results: 10,
            use_reranking: false,
            use_query_expansion: true,
            use_diversification: false,
            show_scores: true,
            show_metadata: true,
            max_content_length: 500,
            custom_metadata: {},
          },
        },
        {
          onSuccess: (data) => {
            // Response structure is { session: { session_id: "...", ... } }
            const newSessionId = data?.session?.session_id || null;
            console.log("Session created:", newSessionId);
            setSessionId(newSessionId);
            // Store in localStorage
            if (newSessionId) {
              localStorage.setItem("chat_session_id", newSessionId);
            }
          },
          onError: (error: any) => {
            console.error("Failed to create session:", error);
            // Reset flag on error so user can try again
            sessionInitialized.current = false;
          },
        }
      );
    }
    // Empty dependency array - only run once on mount
  }, []);

  const handleSendMessage = async (message: string): Promise<string> => {
    try {
      // Detect if user is asking for code generation
      const codeKeywords = ["write", "generate", "create", "code", "script", "example", "show me"];
      const askingForCode = codeKeywords.some(keyword =>
        message.toLowerCase().includes(keyword)
      );

      console.log("Sending chat message with session_id:", sessionId);

      // Send chat request with LLM
      const response = await sendChatMessage({
        message,
        session_id: sessionId || undefined,
        conversation_history: conversationHistory,
        enable_url_scraping: true,
        enable_auto_indexing: true,
        agent_type: askingForCode ? "code" : "general",
      });

      console.log("Chat response received, session_id:", response.data?.session_id);

      if (response.error) {
        throw new Error(response.error);
      }

      const chatResponse = response.data!;

      // Update conversation history
      const newHistory: ChatMessage[] = [
        ...conversationHistory,
        { role: "user", content: message },
        { role: "assistant", content: chatResponse.response },
      ];
      setConversationHistory(newHistory.slice(-20)); // Keep last 20 messages

      // Format response with sources
      let formattedResponse = chatResponse.response;

      // Add metadata about scraped URLs and indexing
      if (chatResponse.scraped_urls.length > 0) {
        formattedResponse += `\n\n---\n**URLs Processed:** ${chatResponse.scraped_urls.length} URLs were scraped and indexed\n`;
        chatResponse.scraped_urls.forEach((url, idx) => {
          formattedResponse += `${idx + 1}. ${url}\n`;
        });
      }

      // Add sources if available
      if (chatResponse.sources.length > 0) {
        formattedResponse += `\n\n---\n**Sources Used:**\n`;
        chatResponse.sources.slice(0, 5).forEach((source, idx) => {
          formattedResponse += `${idx + 1}. ${source.title}`;
          if (source.method) {
            formattedResponse += ` (${source.method})`;
          }
          if (source.url) {
            formattedResponse += ` - ${source.url}`;
          }
          formattedResponse += `\n`;
        });
      }

      // Show info toast about scraping/indexing
      if (chatResponse.scraped_urls.length > 0 || chatResponse.indexed_docs > 0) {
        toast({
          title: "Content Indexed",
          description: `Scraped ${chatResponse.scraped_urls.length} URLs and indexed ${chatResponse.indexed_docs} documents`,
        });
      }

      return formattedResponse;
    } catch (error: any) {
      toast({
        title: "Chat Error",
        description: error.message || "Failed to generate response",
        variant: "destructive",
      });
      throw error;
    }
  };

  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Chat Assistant</h1>
          <p className="text-muted-foreground mt-2">
            Ask questions, provide URLs to scrape, and get AI-powered answers with code examples
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            💡 Try: "I want to use the JSONPlaceholder API (https://jsonplaceholder.typicode.com). Write a Python script to fetch all users."
          </p>
        </div>

        <ChatInterface onSendMessage={handleSendMessage} />
      </div>
    </MainLayout>
  );
}
