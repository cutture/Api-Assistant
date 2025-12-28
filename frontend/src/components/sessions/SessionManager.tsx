/**
 * Session manager component - Create and configure sessions
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreateSession, useSessionStats } from "@/hooks/useSessions";
import { Loader2, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function SessionManager() {
  const [userId, setUserId] = useState("");
  const [ttlMinutes, setTtlMinutes] = useState(60);
  const [useReranking, setUseReranking] = useState(false);
  const [useQueryExpansion, setUseQueryExpansion] = useState(false);

  const { mutate: createSession, isPending } = useCreateSession();
  const { data: stats } = useSessionStats();
  const { toast } = useToast();

  const handleCreateSession = () => {
    createSession(
      {
        user_id: userId.trim() || undefined,
        ttl_minutes: ttlMinutes,
        settings: {
          default_search_mode: "hybrid",
          default_n_results: 10,
          use_reranking: useReranking,
          use_query_expansion: useQueryExpansion,
          use_diversification: false,
          show_scores: true,
          show_metadata: true,
          max_content_length: 500,
          custom_metadata: {},
        },
      },
      {
        onSuccess: (data) => {
          toast({
            title: "Session created",
            description: `Session ID: ${data?.session_id.substring(0, 8)}...`,
          });
          // Reset form
          setUserId("");
          setTtlMinutes(60);
          setUseReranking(false);
          setUseQueryExpansion(false);
        },
        onError: (error: any) => {
          toast({
            title: "Creation failed",
            description: error.message || "Failed to create session",
            variant: "destructive",
          });
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      {/* Session Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{stats.total_sessions}</div>
              <p className="text-xs text-muted-foreground">Total Sessions</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-600">{stats.active_sessions}</div>
              <p className="text-xs text-muted-foreground">Active</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-yellow-600">{stats.inactive_sessions}</div>
              <p className="text-xs text-muted-foreground">Inactive</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-600">{stats.expired_sessions}</div>
              <p className="text-xs text-muted-foreground">Expired</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create Session Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create New Session</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="user-id">User ID (optional)</Label>
            <Input
              id="user-id"
              placeholder="Enter user identifier"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ttl">Session TTL (minutes)</Label>
            <Input
              id="ttl"
              type="number"
              min={1}
              max={10080}
              value={ttlMinutes}
              onChange={(e) => setTtlMinutes(parseInt(e.target.value) || 60)}
            />
            <p className="text-sm text-muted-foreground">
              Time until session expires ({Math.floor(ttlMinutes / 60)} hours {ttlMinutes % 60} minutes)
            </p>
          </div>

          <div className="space-y-3">
            <Label>Default Settings</Label>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="reranking"
                checked={useReranking}
                onCheckedChange={(checked) => setUseReranking(checked as boolean)}
              />
              <label htmlFor="reranking" className="text-sm cursor-pointer">
                Enable re-ranking by default
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="query-expansion"
                checked={useQueryExpansion}
                onCheckedChange={(checked) => setUseQueryExpansion(checked as boolean)}
              />
              <label htmlFor="query-expansion" className="text-sm cursor-pointer">
                Enable query expansion by default
              </label>
            </div>
          </div>

          <Button onClick={handleCreateSession} disabled={isPending} className="w-full">
            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            <Plus className="h-4 w-4 mr-2" />
            Create Session
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
