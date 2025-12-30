/**
 * Chat page - AI-powered chat interface with URL scraping and dynamic indexing
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { useToast } from "@/hooks/use-toast";
import { sendChatMessage, ChatMessage } from "@/lib/api/chat";
import { useState, useEffect, useRef } from "react";
import { createSession, listSessions, getSession } from "@/lib/api/sessions";
import { Session, SessionStatus } from "@/types";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, RefreshCw } from "lucide-react";

export default function ChatPage() {
  const { toast } = useToast();
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSessionReady, setIsSessionReady] = useState(false);
  const [availableSessions, setAvailableSessions] = useState<Session[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const sessionInitialized = useRef(false);

  // Load available sessions on mount
  useEffect(() => {
    loadAvailableSessions();
  }, []);

  // Load sessions and try to restore last used session
  const loadAvailableSessions = async () => {
    setIsLoadingSessions(true);
    try {
      const response = await listSessions(undefined, SessionStatus.ACTIVE);

      if (response.error) {
        throw new Error(response.error);
      }

      const sessions = response.data?.sessions || [];
      setAvailableSessions(sessions);

      // Try to restore last used session from localStorage
      const storedSessionId = localStorage.getItem("chat_session_id");

      if (storedSessionId) {
        // Check if stored session still exists and is active
        const sessionExists = sessions.find(s => s.session_id === storedSessionId);

        if (sessionExists) {
          console.log("Restoring session:", storedSessionId);
          await switchToSession(storedSessionId);
        } else {
          console.log("Stored session no longer exists");
          localStorage.removeItem("chat_session_id");

          // Use most recent session if available
          if (sessions.length > 0) {
            const mostRecent = sessions[0]; // Already sorted by last_accessed
            await switchToSession(mostRecent.session_id);
          }
        }
      } else if (sessions.length > 0) {
        // No stored session, use most recent
        const mostRecent = sessions[0];
        await switchToSession(mostRecent.session_id);
      }
    } catch (error: any) {
      console.error("Failed to load sessions:", error);
      toast({
        title: "Failed to load sessions",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // Switch to a different session
  const switchToSession = async (newSessionId: string) => {
    try {
      console.log("Switching to session:", newSessionId);
      setIsSessionReady(false);

      // Get full session details including conversation history
      const response = await getSession(newSessionId);

      if (response.error) {
        throw new Error(response.error);
      }

      const session = response.data;
      if (!session) {
        throw new Error("Session not found");
      }

      // Load conversation history from session
      const history: ChatMessage[] = session.conversation_history?.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
      })) || [];

      setSessionId(newSessionId);
      setConversationHistory(history);
      setIsSessionReady(true);

      // Store in localStorage
      localStorage.setItem("chat_session_id", newSessionId);

      console.log(`Switched to session ${newSessionId} with ${history.length} messages`);
    } catch (error: any) {
      console.error("Failed to switch session:", error);
      toast({
        title: "Failed to switch session",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  // Create a new session
  const handleCreateNewSession = async () => {
    try {
      console.log("Creating new session...");
      const response = await createSession({
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
      });

      if (response.error) {
        throw new Error(response.error);
      }

      const newSessionId = response.data?.session?.session_id || null;

      if (!newSessionId) {
        throw new Error("Failed to get session ID from response");
      }

      // Clear conversation history for new session
      setConversationHistory([]);

      // Reload sessions list and switch to new session
      await loadAvailableSessions();
      await switchToSession(newSessionId);

      toast({
        title: "Session created",
        description: `New session ${newSessionId.substring(0, 8)}... created`,
      });
    } catch (error: any) {
      console.error("Failed to create session:", error);
      toast({
        title: "Session Creation Failed",
        description: error.message || "Could not create chat session",
        variant: "destructive",
      });
    }
  };

  const handleSendMessage = async (message: string): Promise<string> => {
    try {
      // Wait for session to be ready
      if (!isSessionReady || !sessionId) {
        console.error("Session not ready! isSessionReady:", isSessionReady, "sessionId:", sessionId);
        throw new Error("Session is not ready yet. Please wait...");
      }

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

        {/* Session Selector */}
        <div className="flex items-center gap-3 p-4 bg-muted/30 rounded-lg border">
          <div className="flex-1">
            <label className="text-sm font-medium mb-2 block">
              Active Session
              {sessionId && (
                <span className="ml-2 text-xs text-muted-foreground font-mono">
                  ({sessionId.substring(0, 8)}...)
                </span>
              )}
            </label>
            <Select
              value={sessionId || ""}
              onValueChange={switchToSession}
              disabled={isLoadingSessions || availableSessions.length === 0}
            >
              <SelectTrigger className="w-full bg-background">
                <SelectValue placeholder={isLoadingSessions ? "Loading sessions..." : "Select a session"} />
              </SelectTrigger>
              <SelectContent>
                {availableSessions.map((session) => (
                  <SelectItem key={session.session_id} value={session.session_id}>
                    <div className="flex items-center justify-between gap-4">
                      <span className="font-mono text-xs">
                        {session.session_id.substring(0, 12)}...
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {session.user_id || "No user"}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {session.conversation_history?.length || 0} msgs
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={loadAvailableSessions}
              disabled={isLoadingSessions}
              title="Refresh sessions"
            >
              <RefreshCw className={`h-4 w-4 ${isLoadingSessions ? "animate-spin" : ""}`} />
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleCreateNewSession}
              disabled={isLoadingSessions}
            >
              <Plus className="h-4 w-4 mr-1" />
              New Session
            </Button>
          </div>
        </div>

        {/* Chat status indicator */}
        {!isSessionReady && (
          <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-900 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              {isLoadingSessions ? "Loading sessions..." : "No session selected. Please select or create a session to start chatting."}
            </p>
          </div>
        )}

        <ChatInterface onSendMessage={handleSendMessage} />
      </div>
    </MainLayout>
  );
}
