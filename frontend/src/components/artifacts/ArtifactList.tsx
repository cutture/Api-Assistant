/**
 * ArtifactList Component
 *
 * Displays a list of artifacts with filtering, sorting, and actions.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Download,
  Trash2,
  FileCode,
  FileText,
  Image,
  Archive,
  File,
  RefreshCw,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Artifact,
  listArtifacts,
  downloadArtifact,
  deleteArtifact,
  downloadBlob,
  formatFileSize,
} from "@/lib/api/artifacts";

interface ArtifactListProps {
  sessionId?: string;
  onArtifactSelect?: (artifact: Artifact) => void;
  className?: string;
}

export function ArtifactList({
  sessionId,
  onArtifactSelect,
  className,
}: ArtifactListProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(10);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [languageFilter, setLanguageFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchArtifacts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await listArtifacts({
        session_id: sessionId,
        artifact_type: typeFilter !== "all" ? typeFilter : undefined,
        language: languageFilter !== "all" ? languageFilter : undefined,
        page,
        limit,
      });

      // Filter by search query locally
      let filtered = response.artifacts;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter((a) =>
          a.name.toLowerCase().includes(query)
        );
      }

      setArtifacts(filtered);
      setTotal(response.total);
    } catch (err) {
      setError("Failed to load artifacts");
      console.error("Error fetching artifacts:", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId, typeFilter, languageFilter, page, limit, searchQuery]);

  useEffect(() => {
    fetchArtifacts();
  }, [fetchArtifacts]);

  const handleDownload = async (artifact: Artifact) => {
    try {
      const blob = await downloadArtifact(artifact.id);
      downloadBlob(blob, artifact.name);
    } catch (err) {
      console.error("Error downloading artifact:", err);
    }
  };

  const handleDelete = async (artifact: Artifact) => {
    try {
      await deleteArtifact(artifact.id);
      fetchArtifacts();
    } catch (err) {
      console.error("Error deleting artifact:", err);
    }
  };

  const getTypeIcon = (type: string, mimeType?: string) => {
    switch (type) {
      case "generated":
      case "uploaded":
        if (mimeType?.startsWith("image/")) {
          return <Image className="h-4 w-4" />;
        }
        return <FileCode className="h-4 w-4" />;
      case "output":
        return <Archive className="h-4 w-4" />;
      case "screenshot":
        return <Image className="h-4 w-4" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case "uploaded":
        return "bg-blue-500";
      case "generated":
        return "bg-green-500";
      case "output":
        return "bg-purple-500";
      case "screenshot":
        return "bg-orange-500";
      default:
        return "bg-gray-500";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Artifacts</CardTitle>
          <Button variant="ghost" size="sm" onClick={fetchArtifacts}>
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 mt-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search artifacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="uploaded">Uploaded</SelectItem>
              <SelectItem value="generated">Generated</SelectItem>
              <SelectItem value="output">Output</SelectItem>
              <SelectItem value="screenshot">Screenshot</SelectItem>
            </SelectContent>
          </Select>
          <Select value={languageFilter} onValueChange={setLanguageFilter}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Language" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Languages</SelectItem>
              <SelectItem value="python">Python</SelectItem>
              <SelectItem value="javascript">JavaScript</SelectItem>
              <SelectItem value="typescript">TypeScript</SelectItem>
              <SelectItem value="java">Java</SelectItem>
              <SelectItem value="go">Go</SelectItem>
              <SelectItem value="csharp">C#</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {error ? (
          <div className="p-4 text-center text-red-500">{error}</div>
        ) : loading ? (
          <div className="p-4 text-center text-muted-foreground">Loading...</div>
        ) : artifacts.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No artifacts found
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {artifacts.map((artifact) => (
                  <TableRow
                    key={artifact.id}
                    className={cn(
                      "cursor-pointer hover:bg-muted/50",
                      onArtifactSelect && "cursor-pointer"
                    )}
                    onClick={() => onArtifactSelect?.(artifact)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getTypeIcon(artifact.type, artifact.mime_type)}
                        <span className="font-medium truncate max-w-[200px]">
                          {artifact.name}
                        </span>
                        {artifact.language && (
                          <Badge variant="outline" className="text-xs">
                            {artifact.language}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-white text-xs",
                          getTypeBadgeColor(artifact.type)
                        )}
                      >
                        {artifact.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {artifact.size_bytes
                        ? formatFileSize(artifact.size_bytes)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(artifact.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownload(artifact);
                          }}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Artifact</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to delete "{artifact.name}"?
                                This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDelete(artifact)}
                                className="bg-red-500 hover:bg-red-600"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-2 border-t">
                <div className="text-sm text-muted-foreground">
                  Page {page} of {totalPages} ({total} total)
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default ArtifactList;
