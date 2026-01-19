/**
 * PreviewPanel Component
 *
 * Displays live preview of generated code with iframe embedding.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ExternalLink,
  RefreshCw,
  Maximize2,
  Minimize2,
  X,
  Clock,
  AlertCircle,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PreviewSession {
  id: string;
  url: string;
  status: "starting" | "running" | "stopped" | "error";
  time_remaining_seconds: number;
  error_message?: string;
}

interface PreviewPanelProps {
  preview?: PreviewSession;
  onStart?: () => void;
  onStop?: () => void;
  onRefresh?: () => void;
  isLoading?: boolean;
  className?: string;
}

export function PreviewPanel({
  preview,
  onStart,
  onStop,
  onRefresh,
  isLoading = false,
  className,
}: PreviewPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [iframeKey, setIframeKey] = useState(0);

  // Update countdown timer
  useEffect(() => {
    if (preview?.status === "running") {
      setTimeRemaining(preview.time_remaining_seconds);

      const interval = setInterval(() => {
        setTimeRemaining((t) => Math.max(0, t - 1));
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [preview]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const refreshIframe = useCallback(() => {
    setIframeKey((k) => k + 1);
    onRefresh?.();
  }, [onRefresh]);

  const getStatusIcon = (status: PreviewSession["status"]) => {
    switch (status) {
      case "starting":
        return <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />;
      case "running":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "stopped":
        return <X className="h-4 w-4 text-muted-foreground" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusColor = (status: PreviewSession["status"]) => {
    switch (status) {
      case "starting":
        return "bg-yellow-500";
      case "running":
        return "bg-green-500";
      case "stopped":
        return "bg-gray-500";
      case "error":
        return "bg-red-500";
    }
  };

  if (!preview && !onStart) {
    return null;
  }

  return (
    <Card
      className={cn(
        "overflow-hidden",
        expanded && "fixed inset-4 z-50 flex flex-col",
        className
      )}
    >
      <CardHeader className="pb-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg">Live Preview</CardTitle>
            {preview && (
              <>
                <Badge
                  variant="outline"
                  className={cn("text-white text-xs", getStatusColor(preview.status))}
                >
                  {getStatusIcon(preview.status)}
                  <span className="ml-1 capitalize">{preview.status}</span>
                </Badge>
                {preview.status === "running" && (
                  <Badge variant="outline" className="text-xs">
                    <Clock className="h-3 w-3 mr-1" />
                    {formatTime(timeRemaining)}
                  </Badge>
                )}
              </>
            )}
          </div>
          <div className="flex items-center gap-1">
            {preview?.status === "running" && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={refreshIframe}
                  title="Refresh preview"
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(preview.url, "_blank")}
                  title="Open in new tab"
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* URL bar */}
        {preview?.status === "running" && (
          <div className="flex items-center gap-2 mt-2">
            <div className="flex-1 px-3 py-1.5 bg-muted rounded text-sm font-mono truncate">
              {preview.url}
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className={cn("p-0 flex-1", expanded && "overflow-hidden")}>
        {/* No preview state */}
        {!preview && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <ExternalLink className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No Preview Available</h3>
            <p className="text-muted-foreground mb-4 max-w-sm">
              Start a live preview to see your code running in real-time.
            </p>
            {onStart && (
              <Button onClick={onStart} disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Starting...
                  </>
                ) : (
                  "Start Preview"
                )}
              </Button>
            )}
          </div>
        )}

        {/* Starting state */}
        {preview?.status === "starting" && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Loader2 className="h-12 w-12 text-primary animate-spin mb-4" />
            <h3 className="text-lg font-medium mb-2">Starting Preview Server</h3>
            <p className="text-muted-foreground">
              This may take a few seconds...
            </p>
          </div>
        )}

        {/* Running state - show iframe */}
        {preview?.status === "running" && (
          <div className={cn("w-full bg-white", expanded ? "h-full" : "h-[400px]")}>
            <iframe
              key={iframeKey}
              src={preview.url}
              className="w-full h-full border-0"
              title="Preview"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            />
          </div>
        )}

        {/* Error state */}
        {preview?.status === "error" && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">Preview Failed</h3>
            <p className="text-muted-foreground mb-4 max-w-sm">
              {preview.error_message || "An error occurred while starting the preview."}
            </p>
            {onStart && (
              <Button onClick={onStart} disabled={isLoading} variant="outline">
                Try Again
              </Button>
            )}
          </div>
        )}

        {/* Stopped state */}
        {preview?.status === "stopped" && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <X className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Preview Stopped</h3>
            <p className="text-muted-foreground mb-4">
              The preview server has been stopped.
            </p>
            {onStart && (
              <Button onClick={onStart} disabled={isLoading}>
                Restart Preview
              </Button>
            )}
          </div>
        )}
      </CardContent>

      {/* Controls footer */}
      {preview?.status === "running" && onStop && (
        <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/50">
          <span className="text-xs text-muted-foreground">
            Expires in {formatTime(timeRemaining)}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={onStop}
            className="text-red-500 hover:text-red-600"
          >
            <X className="h-4 w-4 mr-1" />
            Stop Preview
          </Button>
        </div>
      )}
    </Card>
  );
}

export default PreviewPanel;
