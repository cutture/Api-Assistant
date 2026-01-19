/**
 * DiffViewer Component
 *
 * Displays code diffs with syntax highlighting and stats.
 */

"use client";

import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Plus,
  Minus,
  Equal,
  ArrowLeftRight,
  FileCode,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DiffLine {
  type: "equal" | "insert" | "delete";
  old_line_no: number | null;
  new_line_no: number | null;
  content: string;
}

interface DiffStats {
  additions: number;
  deletions: number;
  changes: number;
  total_lines_before: number;
  total_lines_after: number;
}

interface DiffViewerProps {
  oldCode: string;
  newCode: string;
  oldLabel?: string;
  newLabel?: string;
  language?: string;
  className?: string;
}

export function DiffViewer({
  oldCode,
  newCode,
  oldLabel = "Before",
  newLabel = "After",
  language,
  className,
}: DiffViewerProps) {
  const [viewMode, setViewMode] = useState<"unified" | "split">("unified");
  const [expanded, setExpanded] = useState(false);

  // Generate diff lines client-side
  const { diffLines, stats } = useMemo(() => {
    const oldLines = oldCode.split("\n");
    const newLines = newCode.split("\n");

    // Simple line-by-line diff (in production, use a proper diff library)
    const lines: DiffLine[] = [];
    let additions = 0;
    let deletions = 0;

    // LCS-based diff algorithm (simplified)
    const maxLen = Math.max(oldLines.length, newLines.length);

    let oldIdx = 0;
    let newIdx = 0;

    while (oldIdx < oldLines.length || newIdx < newLines.length) {
      const oldLine = oldLines[oldIdx];
      const newLine = newLines[newIdx];

      if (oldIdx >= oldLines.length) {
        // Only new lines left
        lines.push({
          type: "insert",
          old_line_no: null,
          new_line_no: newIdx + 1,
          content: newLine,
        });
        additions++;
        newIdx++;
      } else if (newIdx >= newLines.length) {
        // Only old lines left
        lines.push({
          type: "delete",
          old_line_no: oldIdx + 1,
          new_line_no: null,
          content: oldLine,
        });
        deletions++;
        oldIdx++;
      } else if (oldLine === newLine) {
        // Lines match
        lines.push({
          type: "equal",
          old_line_no: oldIdx + 1,
          new_line_no: newIdx + 1,
          content: oldLine,
        });
        oldIdx++;
        newIdx++;
      } else {
        // Check if line was deleted or modified
        const newLineInOld = oldLines.slice(oldIdx + 1).indexOf(newLine);
        const oldLineInNew = newLines.slice(newIdx + 1).indexOf(oldLine);

        if (newLineInOld === -1 && oldLineInNew === -1) {
          // Line was modified - show as delete + insert
          lines.push({
            type: "delete",
            old_line_no: oldIdx + 1,
            new_line_no: null,
            content: oldLine,
          });
          deletions++;
          lines.push({
            type: "insert",
            old_line_no: null,
            new_line_no: newIdx + 1,
            content: newLine,
          });
          additions++;
          oldIdx++;
          newIdx++;
        } else if (oldLineInNew !== -1) {
          // New line inserted
          lines.push({
            type: "insert",
            old_line_no: null,
            new_line_no: newIdx + 1,
            content: newLine,
          });
          additions++;
          newIdx++;
        } else {
          // Old line deleted
          lines.push({
            type: "delete",
            old_line_no: oldIdx + 1,
            new_line_no: null,
            content: oldLine,
          });
          deletions++;
          oldIdx++;
        }
      }
    }

    return {
      diffLines: lines,
      stats: {
        additions,
        deletions,
        changes: Math.min(additions, deletions),
        total_lines_before: oldLines.length,
        total_lines_after: newLines.length,
      } as DiffStats,
    };
  }, [oldCode, newCode]);

  const getLineClass = (type: DiffLine["type"]) => {
    switch (type) {
      case "insert":
        return "bg-green-500/10 border-l-2 border-green-500";
      case "delete":
        return "bg-red-500/10 border-l-2 border-red-500";
      default:
        return "";
    }
  };

  const getLineIcon = (type: DiffLine["type"]) => {
    switch (type) {
      case "insert":
        return <Plus className="h-3 w-3 text-green-500" />;
      case "delete":
        return <Minus className="h-3 w-3 text-red-500" />;
      default:
        return <Equal className="h-3 w-3 text-muted-foreground" />;
    }
  };

  return (
    <Card className={cn("overflow-hidden", expanded && "fixed inset-4 z-50", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ArrowLeftRight className="h-5 w-5" />
            <CardTitle className="text-lg">Code Diff</CardTitle>
            {language && (
              <Badge variant="outline" className="text-xs">
                {language}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Stats badges */}
            {stats.additions > 0 && (
              <Badge variant="outline" className="text-green-500 border-green-500">
                +{stats.additions}
              </Badge>
            )}
            {stats.deletions > 0 && (
              <Badge variant="outline" className="text-red-500 border-red-500">
                -{stats.deletions}
              </Badge>
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

        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "unified" | "split")}>
          <TabsList className="h-8">
            <TabsTrigger value="unified" className="text-xs">
              Unified
            </TabsTrigger>
            <TabsTrigger value="split" className="text-xs">
              Split
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>

      <CardContent className="p-0">
        {viewMode === "unified" ? (
          <div className="overflow-auto max-h-[500px]">
            <table className="w-full text-sm font-mono">
              <thead className="sticky top-0 bg-muted text-muted-foreground">
                <tr>
                  <th className="w-12 px-2 py-1 text-right border-r">{oldLabel}</th>
                  <th className="w-12 px-2 py-1 text-right border-r">{newLabel}</th>
                  <th className="w-6 px-1 py-1"></th>
                  <th className="px-2 py-1 text-left">Code</th>
                </tr>
              </thead>
              <tbody>
                {diffLines.map((line, idx) => (
                  <tr key={idx} className={getLineClass(line.type)}>
                    <td className="w-12 px-2 py-0.5 text-right text-muted-foreground border-r text-xs">
                      {line.old_line_no || ""}
                    </td>
                    <td className="w-12 px-2 py-0.5 text-right text-muted-foreground border-r text-xs">
                      {line.new_line_no || ""}
                    </td>
                    <td className="w-6 px-1 py-0.5 text-center">
                      {getLineIcon(line.type)}
                    </td>
                    <td className="px-2 py-0.5 whitespace-pre">
                      {line.content || " "}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-2 divide-x overflow-auto max-h-[500px]">
            {/* Old code */}
            <div>
              <div className="sticky top-0 bg-muted px-2 py-1 text-sm font-medium border-b">
                <FileCode className="h-4 w-4 inline mr-1" />
                {oldLabel}
              </div>
              <div className="text-sm font-mono">
                {oldCode.split("\n").map((line, idx) => {
                  const diffLine = diffLines.find(
                    (d) => d.old_line_no === idx + 1 && d.type !== "insert"
                  );
                  const isDeleted = diffLine?.type === "delete";

                  return (
                    <div
                      key={idx}
                      className={cn(
                        "flex",
                        isDeleted && "bg-red-500/10 border-l-2 border-red-500"
                      )}
                    >
                      <span className="w-10 px-2 py-0.5 text-right text-muted-foreground text-xs border-r">
                        {idx + 1}
                      </span>
                      <span className="px-2 py-0.5 whitespace-pre flex-1">
                        {line || " "}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* New code */}
            <div>
              <div className="sticky top-0 bg-muted px-2 py-1 text-sm font-medium border-b">
                <FileCode className="h-4 w-4 inline mr-1" />
                {newLabel}
              </div>
              <div className="text-sm font-mono">
                {newCode.split("\n").map((line, idx) => {
                  const diffLine = diffLines.find(
                    (d) => d.new_line_no === idx + 1 && d.type !== "delete"
                  );
                  const isInserted = diffLine?.type === "insert";

                  return (
                    <div
                      key={idx}
                      className={cn(
                        "flex",
                        isInserted && "bg-green-500/10 border-l-2 border-green-500"
                      )}
                    >
                      <span className="w-10 px-2 py-0.5 text-right text-muted-foreground text-xs border-r">
                        {idx + 1}
                      </span>
                      <span className="px-2 py-0.5 whitespace-pre flex-1">
                        {line || " "}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </CardContent>

      {/* Stats footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t bg-muted/50 text-xs text-muted-foreground">
        <span>
          {stats.total_lines_before} lines → {stats.total_lines_after} lines
        </span>
        <span>
          {stats.additions} additions, {stats.deletions} deletions
        </span>
      </div>
    </Card>
  );
}

export default DiffViewer;
