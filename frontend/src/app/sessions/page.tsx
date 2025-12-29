/**
 * Sessions page - Session management and history
 */

"use client";

import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { SessionManager } from "@/components/sessions/SessionManager";
import { SessionList } from "@/components/sessions/SessionList";
import { useSession, useUpdateSession } from "@/hooks/useSessions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { ArrowLeft, Edit, Save, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useToast } from "@/hooks/use-toast";

export default function SessionsPage() {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editFormData, setEditFormData] = useState({
    user_id: "",
    use_reranking: false,
    use_query_expansion: false,
  });
  const { data: selectedSession } = useSession(selectedSessionId || "");
  const { mutate: updateSession, isPending: isUpdating } = useUpdateSession();
  const { toast } = useToast();

  const handleBackToList = () => {
    setSelectedSessionId(null);
    setIsEditing(false);
  };

  const handleStartEdit = () => {
    if (selectedSession) {
      setEditFormData({
        user_id: selectedSession.user_id || "",
        use_reranking: selectedSession.settings.use_reranking,
        use_query_expansion: selectedSession.settings.use_query_expansion,
      });
      setIsEditing(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleSaveEdit = () => {
    if (!selectedSessionId) return;

    updateSession(
      {
        sessionId: selectedSessionId,
        updates: {
          user_id: editFormData.user_id || undefined,
          settings: {
            default_search_mode: selectedSession?.settings.default_search_mode || "hybrid",
            default_n_results: selectedSession?.settings.default_n_results || 10,
            use_reranking: editFormData.use_reranking,
            use_query_expansion: editFormData.use_query_expansion,
            use_diversification: selectedSession?.settings.use_diversification || false,
            show_scores: selectedSession?.settings.show_scores ?? true,
            show_metadata: selectedSession?.settings.show_metadata ?? true,
            max_content_length: selectedSession?.settings.max_content_length || 500,
            custom_metadata: selectedSession?.settings.custom_metadata || {},
          },
        },
      },
      {
        onSuccess: () => {
          toast({
            title: "Session updated",
            description: "Session metadata has been updated successfully",
          });
          setIsEditing(false);
        },
        onError: (error: any) => {
          toast({
            title: "Update failed",
            description: error.message || "Failed to update session",
            variant: "destructive",
          });
        },
      }
    );
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
                  <div>
                    <span>Session Details</span>
                    <span className="block text-sm font-mono text-muted-foreground mt-1">
                      {selectedSession.session_id}
                    </span>
                  </div>
                  {!isEditing ? (
                    <Button variant="outline" size="sm" onClick={handleStartEdit}>
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  ) : (
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCancelEdit}
                        disabled={isUpdating}
                      >
                        <X className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                      <Button size="sm" onClick={handleSaveEdit} disabled={isUpdating}>
                        <Save className="h-4 w-4 mr-2" />
                        Save
                      </Button>
                    </div>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {!isEditing ? (
                  // Display Mode
                  <>
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
                        <p className="text-sm font-medium">Expires</p>
                        <p className="text-sm text-muted-foreground">
                          {selectedSession.expires_at
                            ? formatDistanceToNow(new Date(selectedSession.expires_at), {
                                addSuffix: true,
                              })
                            : "Never"}
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
                    </div>

                    {/* Settings */}
                    <div>
                      <p className="text-sm font-medium mb-2">Settings</p>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          Search Mode:{" "}
                          <span className="text-muted-foreground">
                            {selectedSession.settings.default_search_mode}
                          </span>
                        </div>
                        <div>
                          Results Limit:{" "}
                          <span className="text-muted-foreground">
                            {selectedSession.settings.default_n_results}
                          </span>
                        </div>
                        <div>
                          Re-ranking:{" "}
                          <span className="text-muted-foreground">
                            {selectedSession.settings.use_reranking ? "Enabled" : "Disabled"}
                          </span>
                        </div>
                        <div>
                          Query Expansion:{" "}
                          <span className="text-muted-foreground">
                            {selectedSession.settings.use_query_expansion
                              ? "Enabled"
                              : "Disabled"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  // Edit Mode
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="edit-user-id">User ID (optional)</Label>
                      <Input
                        id="edit-user-id"
                        placeholder="Enter user identifier"
                        value={editFormData.user_id}
                        onChange={(e) =>
                          setEditFormData({ ...editFormData, user_id: e.target.value })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="edit-ttl">TTL (minutes)</Label>
                      <Input
                        id="edit-ttl"
                        type="number"
                        min={1}
                        max={10080}
                        value={editFormData.ttl_minutes}
                        onChange={(e) =>
                          setEditFormData({
                            ...editFormData,
                            ttl_minutes: parseInt(e.target.value) || 60,
                          })
                        }
                      />
                    </div>

                    <div className="space-y-3">
                      <Label>Settings</Label>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="edit-reranking"
                          checked={editFormData.use_reranking}
                          onCheckedChange={(checked: boolean) =>
                            setEditFormData({
                              ...editFormData,
                              use_reranking: checked,
                            })
                          }
                        />
                        <label htmlFor="edit-reranking" className="text-sm cursor-pointer">
                          Enable re-ranking
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="edit-query-expansion"
                          checked={editFormData.use_query_expansion}
                          onCheckedChange={(checked: boolean) =>
                            setEditFormData({
                              ...editFormData,
                              use_query_expansion: checked,
                            })
                          }
                        />
                        <label htmlFor="edit-query-expansion" className="text-sm cursor-pointer">
                          Enable query expansion
                        </label>
                      </div>
                    </div>
                  </div>
                )}

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
