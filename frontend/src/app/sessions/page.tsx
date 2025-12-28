/**
 * Sessions page - Session management and history
 */

"use client";

import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { SessionManager } from "@/components/sessions/SessionManager";
import { SessionList } from "@/components/sessions/SessionList";
import { useSession } from "@/hooks/useSessions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function SessionsPage() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const { data: selectedSession } = useSession(selectedSessionId || "");

  const handleBackToList = () => {
    setSelectedSessionId(null);
  };

  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Session Management</h1>
          <p className="text-muted-foreground mt-2">
            Create and manage user sessions with isolated conversation history and settings
          </p>
        </div>

        {selectedSessionId && selectedSession ? (
          // Session Detail View
          <div className="space-y-4">
            <Button variant="outline" onClick={handleBackToList}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Sessions
            </Button>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Session Details</span>
                  <span className="text-sm font-mono text-muted-foreground">
                    {selectedSession.session_id}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Session Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium">Status</p>
                    <p className="text-sm text-muted-foreground capitalize">
                      {selectedSession.status}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">User ID</p>
                    <p className="text-sm text-muted-foreground">
                      {selectedSession.user_id || "Anonymous"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Created</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(selectedSession.created_at), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Last Accessed</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(selectedSession.last_accessed), {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                </div>

                {/* Settings */}
                <div>
                  <p className="text-sm font-medium mb-2">Settings</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      Search Mode: <span className="text-muted-foreground">{selectedSession.settings.default_search_mode}</span>
                    </div>
                    <div>
                      Results Limit: <span className="text-muted-foreground">{selectedSession.settings.default_n_results}</span>
                    </div>
                    <div>
                      Re-ranking: <span className="text-muted-foreground">{selectedSession.settings.use_reranking ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div>
                      Query Expansion: <span className="text-muted-foreground">{selectedSession.settings.use_query_expansion ? "Enabled" : "Disabled"}</span>
                    </div>
                  </div>
                </div>

                {/* Conversation History */}
                <div>
                  <p className="text-sm font-medium mb-2">
                    Conversation History ({selectedSession.conversation_history.length} messages)
                  </p>
                  {selectedSession.conversation_history.length > 0 ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {selectedSession.conversation_history.map((msg, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-md ${
                            msg.role === "user"
                              ? "bg-primary/10"
                              : msg.role === "assistant"
                              ? "bg-secondary/50"
                              : "bg-muted"
                          }`}
                        >
                          <div className="flex justify-between items-start mb-1">
                            <span className="text-xs font-medium capitalize">{msg.role}</span>
                            <span className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true })}
                            </span>
                          </div>
                          <p className="text-sm">{msg.content}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No messages yet</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          // List View
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Create Session */}
            <div className="lg:col-span-1">
              <SessionManager />
            </div>

            {/* Session List */}
            <div className="lg:col-span-2">
              <SessionList onSelectSession={setSelectedSessionId} />
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
