/**
 * Chat page - AI-powered chat interface with URL scraping and dynamic indexing
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { useToast } from "@/hooks/use-toast";
import { sendChatMessage, ChatMessage } from "@/lib/api/chat";
import { useState, useEffect, useRef } from "react";
import { createSession, listSessions, getSession, updateSession } from "@/lib/api/sessions";
import { Session, SessionStatus } from "@/types";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, RefreshCw, MoreVertical, Eye, Trash2, StopCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { useClearSessionHistory } from "@/hooks/useSessions";

export default function ChatPage() {
  const { toast } = useToast();
  const router = useRouter();
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSessionReady, setIsSessionReady] = useState(false);
  const [availableSessions, setAvailableSessions] = useState<Session[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const sessionInitialized = useRef(false);

  // State for alert dialogs
  const [showClearHistoryDialog, setShowClearHistoryDialog] = useState(false);
  const [showEndSessionDialog, setShowEndSessionDialog] = useState(false);

  // Hook for clearing session history
  const { mutate: clearHistory, isPending: isClearingHistory } = useClearSessionHistory();

  // Key to force ChatInterface re-mount when history is cleared
  const [chatKey, setChatKey] = useState(0);

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

      // If no sessions exist, create a default one
      if (sessions.length === 0) {
        console.log("No sessions found, creating default session...");
        await createDefaultSession();
        return; // createDefaultSession will call loadAvailableSessions again
      }

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

  // Create default session for new users
  const createDefaultSession = async () => {
    try {
      console.log("Creating default session...");
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

      console.log("Default session created:", newSessionId);

      // Reload sessions and switch to the new one
      await loadAvailableSessions();
    } catch (error: any) {
      console.error("Failed to create default session:", error);
      toast({
        title: "Failed to create default session",
        description: error.message,
        variant: "destructive",
      });
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

  // Handler for View Session menu option
  const handleViewSession = () => {
    if (!sessionId) return;
    router.push(`/sessions?selected=${sessionId}`);
  };

  // Handler for Clear Conversation History menu option
  const handleClearHistoryClick = () => {
    setShowClearHistoryDialog(true);
  };

  const confirmClearHistory = () => {
    if (!sessionId) return;

    clearHistory(sessionId, {
      onSuccess: () => {
        // Clear local chat UI
        setConversationHistory([]);
        // Force ChatInterface to re-mount with empty messages
        setChatKey(prev => prev + 1);
        toast({
          title: "History cleared",
          description: "All conversation history has been permanently deleted from this session.",
        });
        setShowClearHistoryDialog(false);
      },
      onError: (error: any) => {
        toast({
          title: "Failed to clear history",
          description: error.message || "An error occurred while clearing history",
          variant: "destructive",
        });
        setShowClearHistoryDialog(false);
      },
    });
  };

  // Handler for End Session menu option
  const handleEndSessionClick = () => {
    setShowEndSessionDialog(true);
  };

  const confirmEndSession = async () => {
    if (!sessionId) return;

    try {
      // Set current session to INACTIVE
      const updateResponse = await updateSession(sessionId, {
        status: SessionStatus.INACTIVE,
      });

      if (updateResponse.error) {
        throw new Error(updateResponse.error);
      }

      // Create new session
      const createResponse = await createSession({
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

      if (createResponse.error) {
        throw new Error(createResponse.error);
      }

      const newSessionId = createResponse.data?.session?.session_id || null;

      if (!newSessionId) {
        throw new Error("Failed to get session ID from response");
      }

      // Clear UI and switch to new session
      setConversationHistory([]);
      setChatKey(prev => prev + 1); // Force ChatInterface to re-mount
      setSessionId(newSessionId);
      localStorage.setItem("chat_session_id", newSessionId);
      setIsSessionReady(true);

      // Reload available sessions
      await loadAvailableSessions();

      toast({
        title: "Session ended",
        description: "Previous session has been ended. A new session has been created.",
      });
      setShowEndSessionDialog(false);
    } catch (error: any) {
      toast({
        title: "Failed to end session",
        description: error.message || "An error occurred while ending the session",
        variant: "destructive",
      });
      setShowEndSessionDialog(false);
    }
  };

  const handleSendMessage = async (message: string, files?: File[]): Promise<string> => {
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

      console.log("Sending chat message with session_id:", sessionId, "files:", files?.length || 0);

      // Send chat request with LLM (and files if present)
      const response = await sendChatMessage({
        message,
        session_id: sessionId || undefined,
        conversation_history: conversationHistory,
        enable_url_scraping: true,
        enable_auto_indexing: true,
        agent_type: askingForCode ? "code" : "general",
        files,
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
        chatResponse.scraped_urls.forEach((url: string, idx: number) => {
          formattedResponse += `${idx + 1}. ${url}\n`;
        });
      }

      // Add sources if available
      if (chatResponse.sources.length > 0) {
        formattedResponse += `\n\n---\n**Sources Used:**\n`;
        chatResponse.sources.slice(0, 5).forEach((source: any, idx: number) => {
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

      // Show info toast about scraping/indexing/file upload
      if (chatResponse.scraped_urls.length > 0 || chatResponse.indexed_docs > 0 || (files && files.length > 0)) {
        const parts = [];
        if (chatResponse.scraped_urls.length > 0) {
          parts.push(`Scraped ${chatResponse.scraped_urls.length} URL${chatResponse.scraped_urls.length > 1 ? 's' : ''}`);
        }
        if (files && files.length > 0) {
          parts.push(`Uploaded ${files.length} file${files.length > 1 ? 's' : ''}`);
        }
        if (chatResponse.indexed_docs > 0) {
          parts.push(`Indexed ${chatResponse.indexed_docs} document${chatResponse.indexed_docs > 1 ? 's' : ''}`);
        }

        toast({
          title: "Content Processed",
          description: parts.join(', '),
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
            Ask questions, upload documents, provide URLs to scrape, and get AI-powered answers with code examples
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            💡 Try: "I want to use the JSONPlaceholder API (https://jsonplaceholder.typicode.com). Write a Python script to fetch all users."
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            📎 Upload PDFs, API specs, or text files to get context-aware answers
          </p>
        </div>

        {/* Session Selector */}
        <div className="flex items-center gap-3 p-4 bg-muted/30 rounded-lg border">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium">
                Active Session
                {sessionId && (
                  <span className="ml-2 text-xs text-muted-foreground font-mono">
                    ({sessionId.substring(0, 8)}...)
                  </span>
                )}
              </label>
              {sessionId && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={handleViewSession}>
                      <Eye className="h-4 w-4 mr-2" />
                      View Session
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleClearHistoryClick}>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Clear Conversation History
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={handleEndSessionClick}>
                      <StopCircle className="h-4 w-4 mr-2" />
                      End Session
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
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

        <ChatInterface
          key={`${sessionId || "no-session"}-${chatKey}`} // Force remount when session changes or history is cleared
          onSendMessage={handleSendMessage}
          initialMessages={conversationHistory.map((msg) => ({
            role: msg.role as "user" | "assistant" | "system",
            content: msg.content,
            timestamp: new Date().toISOString(),
          }))}
        />

        {/* Clear History Confirmation Dialog */}
        <AlertDialog open={showClearHistoryDialog} onOpenChange={setShowClearHistoryDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear Conversation History?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete all messages in this session. This action cannot be undone.
                The session itself will be preserved, but all conversation history will be lost.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isClearingHistory}>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmClearHistory} disabled={isClearingHistory}>
                {isClearingHistory ? "Clearing..." : "Clear History"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* End Session Confirmation Dialog */}
        <AlertDialog open={showEndSessionDialog} onOpenChange={setShowEndSessionDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>End This Session?</AlertDialogTitle>
              <AlertDialogDescription>
                This will mark the current session as inactive and create a new session for you.
                All conversation history will be preserved in the ended session, and you can reactivate it later from the Sessions page.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmEndSession}>
                End Session
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </MainLayout>
  );
}
