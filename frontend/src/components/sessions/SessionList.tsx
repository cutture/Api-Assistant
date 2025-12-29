/**
 * Session list component - Display and manage sessions
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useListSessions, useDeleteSession } from "@/hooks/useSessions";
import { Trash2, Eye, Clock, User } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { SessionStatus } from "@/types";
import { formatDistanceToNow } from "date-fns";

export interface SessionListProps {
  onSelectSession?: (sessionId: string) => void;
}

export function SessionList({ onSelectSession }: SessionListProps) {
  const [selectedStatus, setSelectedStatus] = useState<SessionStatus | undefined>();
  const { data: sessionsData, isLoading } = useListSessions(undefined, selectedStatus);
  const { mutate: deleteSession } = useDeleteSession();
  const { toast } = useToast();

  const handleDelete = (sessionId: string) => {
    if (!confirm("Are you sure you want to delete this session?")) {
      return;
    }

    deleteSession(sessionId, {
      onSuccess: () => {
        toast({
          title: "Session deleted",
          description: "Session has been removed successfully",
        });
      },
      onError: (error: any) => {
        toast({
          title: "Delete failed",
          description: error.message || "Failed to delete session",
          variant: "destructive",
        });
      },
    });
  };

  const getStatusBadgeVariant = (status: SessionStatus) => {
    switch (status) {
      case SessionStatus.ACTIVE:
        return "default";
      case SessionStatus.INACTIVE:
        return "secondary";
      case SessionStatus.EXPIRED:
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Sessions</CardTitle>
          <div className="flex space-x-2">
            <Button
              variant={selectedStatus === undefined ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedStatus(undefined)}
            >
              All
            </Button>
            <Button
              variant={selectedStatus === SessionStatus.ACTIVE ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedStatus(SessionStatus.ACTIVE)}
            >
              Active
            </Button>
            <Button
              variant={selectedStatus === SessionStatus.INACTIVE ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedStatus(SessionStatus.INACTIVE)}
            >
              Inactive
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="text-center py-8 text-muted-foreground">Loading sessions...</div>
        )}

        {!isLoading && (!sessionsData?.sessions || sessionsData.sessions.length === 0) && (
          <div className="text-center py-8 text-muted-foreground">
            No sessions found. Create a new session to get started.
          </div>
        )}

        {!isLoading && sessionsData?.sessions && sessionsData.sessions.length > 0 && (
          <div className="space-y-3">
            {sessionsData.sessions.map((session) => (
              <div
                key={session.session_id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1 space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium font-mono text-sm">
                      {session.session_id ? session.session_id.substring(0, 8) : "unknown"}...
                    </span>
                    <Badge variant={getStatusBadgeVariant(session.status)}>
                      {session.status}
                    </Badge>
                  </div>

                  <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                    {session.user_id && (
                      <div className="flex items-center space-x-1">
                        <User className="h-3 w-3" />
                        <span>{session.user_id}</span>
                      </div>
                    )}
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span>
                        {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <span>{session.conversation_history?.length || 0} messages</span>
                  </div>
                </div>

                <div className="flex space-x-2">
                  {onSelectSession && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onSelectSession(session.session_id)}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(session.session_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
