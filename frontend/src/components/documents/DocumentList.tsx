/**
 * Document list view with delete functionality
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Trash2, Search, FileText, Globe, Code, AlertCircle, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { useCollectionStats, useDeleteDocument, useBulkDeleteDocuments } from "@/hooks/useDocuments";
import { useToast } from "@/hooks/use-toast";
import { exportDocuments } from "@/lib/api/documents";
import { DocumentDetailsModal } from "./DocumentDetailsModal";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type SortField = "name" | "format" | "size" | "chunks";
type SortDirection = "asc" | "desc";

export function DocumentList() {
  const { data: stats, isLoading } = useCollectionStats();
  const { mutate: deleteDocument } = useDeleteDocument();
  const { mutate: bulkDelete } = useBulkDeleteDocuments();
  const { toast } = useToast();

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [documents, setDocuments] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [displayLimit, setDisplayLimit] = useState<number | "all">(20);

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      const response = await exportDocuments(); // Load all documents (no limit)
      if (response.data) {
        setDocuments(response.data);
      }
    } catch (error: any) {
      toast({
        title: "Error loading documents",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleDelete = (documentId: string) => {
    deleteDocument(documentId, {
      onSuccess: () => {
        toast({
          title: "Document deleted",
          description: "Document removed successfully",
        });
        loadDocuments();
      },
      onError: (error: any) => {
        toast({
          title: "Delete failed",
          description: error.message,
          variant: "destructive",
        });
      },
    });
  };

  const handleRowClick = (doc: any) => {
    setSelectedDocument(doc);
    setIsModalOpen(true);
  };

  const handleUpdateMetadata = (documentId: string, metadata: any) => {
    // Update the document in the local state
    setDocuments((prev) =>
      prev.map((doc) =>
        doc.id === documentId ? { ...doc, metadata } : doc
      )
    );
  };

  const handleBulkDelete = () => {
    if (selectedIds.length === 0) return;

    bulkDelete(selectedIds, {
      onSuccess: () => {
        toast({
          title: "Documents deleted",
          description: `${selectedIds.length} documents removed`,
        });
        setSelectedIds([]);
        loadDocuments();
      },
      onError: (error: any) => {
        toast({
          title: "Bulk delete failed",
          description: error.message,
          variant: "destructive",
        });
      },
    });
  };

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  // Get document name from metadata
  const getDocumentName = (doc: any): string => {
    return (
      doc.metadata?.endpoint ||
      doc.metadata?.path ||
      doc.metadata?.api_title ||
      doc.metadata?.source_file ||
      "Untitled"
    );
  };

  // Get document size in bytes
  const getDocumentSize = (doc: any): number => {
    return doc.content?.length || 0;
  };

  // Format size for display
  const formatSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  // Get chunk count
  const getChunkCount = (doc: any): number => {
    return doc.metadata?.total_chunks || 1;
  };

  // Filter and sort all documents
  const filteredAndSortedDocuments = documents
    .filter((doc) => {
      if (!searchQuery) return true;
      const search = searchQuery.toLowerCase();
      return (
        doc.metadata?.endpoint?.toLowerCase().includes(search) ||
        doc.metadata?.api_name?.toLowerCase().includes(search) ||
        doc.metadata?.method?.toLowerCase().includes(search) ||
        doc.content?.toLowerCase().includes(search)
      );
    })
    .sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case "name":
          aValue = getDocumentName(a).toLowerCase();
          bValue = getDocumentName(b).toLowerCase();
          break;
        case "format":
          aValue = a.metadata?.source || "";
          bValue = b.metadata?.source || "";
          break;
        case "size":
          aValue = getDocumentSize(a);
          bValue = getDocumentSize(b);
          break;
        case "chunks":
          aValue = getChunkCount(a);
          bValue = getChunkCount(b);
          break;
      }

      if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
      if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

  // Apply display limit
  const displayedDocuments = displayLimit === "all"
    ? filteredAndSortedDocuments
    : filteredAndSortedDocuments.slice(0, displayLimit);
  const totalFilteredCount = filteredAndSortedDocuments.length;
  const displayedCount = displayedDocuments.length;

  const toggleSelectAll = () => {
    if (selectedIds.length === displayedDocuments.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(displayedDocuments.map((doc) => doc.id));
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case "openapi":
        return Globe;
      case "graphql":
        return Code;
      case "postman":
        return FileText;
      default:
        return FileText;
    }
  };

  // Handle sort column click
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction if clicking the same field
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      // New field, default to ascending
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Get sort icon for column header
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 ml-1 opacity-40" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="h-4 w-4 ml-1" />
    ) : (
      <ArrowDown className="h-4 w-4 ml-1" />
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Document Library</CardTitle>
              <CardDescription>
                {isLoading ? "Loading..." : `${stats?.collection?.total_documents || 0} documents indexed`}
              </CardDescription>
            </div>
            <Button onClick={loadDocuments} disabled={loadingDocs}>
              {loadingDocs ? "Loading..." : "Load Documents"}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Search and Bulk Actions */}
      {documents.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  Show:
                </span>
                <Select
                  value={displayLimit.toString()}
                  onValueChange={(value) => setDisplayLimit(value === "all" ? "all" : parseInt(value))}
                >
                  <SelectTrigger className="w-[100px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="all">All</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {selectedIds.length > 0 && (
                <Button
                  variant="destructive"
                  onClick={handleBulkDelete}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete ({selectedIds.length})
                </Button>
              )}
            </div>
            {totalFilteredCount > 0 && (
              <div className="mt-3 text-sm text-muted-foreground">
                Showing {displayedCount} of {totalFilteredCount} documents
                {searchQuery && " (filtered)"}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Document List */}
      {documents.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            {/* Select All Row */}
            <div className="flex items-center space-x-3 p-4 border-b bg-muted/30">
              <Checkbox
                checked={selectedIds.length === displayedDocuments.length && displayedDocuments.length > 0}
                onCheckedChange={toggleSelectAll}
              />
              <span className="text-sm font-medium">
                {selectedIds.length > 0
                  ? `${selectedIds.length} selected`
                  : "Select all"}
              </span>
            </div>

            {displayedDocuments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-muted/50 border-b">
                    <tr>
                      <th className="w-12 p-3"></th>
                      <th
                        className="text-left p-3 font-medium text-sm cursor-pointer hover:bg-muted/70 transition-colors"
                        onClick={() => handleSort("name")}
                      >
                        <div className="flex items-center">
                          Name
                          {getSortIcon("name")}
                        </div>
                      </th>
                      <th
                        className="text-left p-3 font-medium text-sm cursor-pointer hover:bg-muted/70 transition-colors"
                        onClick={() => handleSort("format")}
                      >
                        <div className="flex items-center">
                          Format
                          {getSortIcon("format")}
                        </div>
                      </th>
                      <th
                        className="text-left p-3 font-medium text-sm cursor-pointer hover:bg-muted/70 transition-colors"
                        onClick={() => handleSort("size")}
                      >
                        <div className="flex items-center">
                          Size
                          {getSortIcon("size")}
                        </div>
                      </th>
                      <th
                        className="text-left p-3 font-medium text-sm cursor-pointer hover:bg-muted/70 transition-colors"
                        onClick={() => handleSort("chunks")}
                      >
                        <div className="flex items-center">
                          Chunks
                          {getSortIcon("chunks")}
                        </div>
                      </th>
                      <th className="w-16 p-3 text-center font-medium text-sm">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {displayedDocuments.map((doc) => {
                      const SourceIcon = getSourceIcon(doc.metadata?.source || "");
                      return (
                        <tr
                          key={doc.id}
                          className="hover:bg-muted/50 transition-colors cursor-pointer"
                          onClick={() => handleRowClick(doc)}
                        >
                          <td className="p-3" onClick={(e) => e.stopPropagation()}>
                            <Checkbox
                              checked={selectedIds.includes(doc.id)}
                              onCheckedChange={() => toggleSelection(doc.id)}
                            />
                          </td>
                          <td className="p-3">
                            <div className="flex items-center space-x-2">
                              <SourceIcon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              <div className="min-w-0">
                                <div className="flex items-center space-x-2 flex-wrap">
                                  <p className="text-sm font-medium truncate">
                                    {getDocumentName(doc)}
                                  </p>
                                  {doc.metadata?.method && (
                                    <Badge variant="outline" className="text-xs">
                                      {doc.metadata.method}
                                    </Badge>
                                  )}
                                </div>
                                {doc.metadata?.api_name && (
                                  <p className="text-xs text-muted-foreground truncate">
                                    {doc.metadata.api_name}
                                  </p>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="p-3">
                            <Badge variant="secondary" className="text-xs">
                              {doc.metadata?.source || "unknown"}
                            </Badge>
                          </td>
                          <td className="p-3">
                            <span className="text-sm text-muted-foreground">
                              {formatSize(getDocumentSize(doc))}
                            </span>
                          </td>
                          <td className="p-3">
                            <span className="text-sm text-muted-foreground">
                              {getChunkCount(doc)}
                            </span>
                          </td>
                          <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(doc.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-12 text-center text-muted-foreground">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No documents match your search</p>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        !loadingDocs && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Click "Load Documents" to view your indexed documents</p>
            </CardContent>
          </Card>
        )
      )}

      {/* Document Details Modal */}
      <DocumentDetailsModal
        document={selectedDocument}
        open={isModalOpen}
        onOpenChange={setIsModalOpen}
        onDelete={handleDelete}
        onUpdate={handleUpdateMetadata}
      />
    </div>
  );
}
