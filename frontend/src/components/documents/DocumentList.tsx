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
import { Trash2, Search, FileText, Globe, Code, AlertCircle } from "lucide-react";
import { useCollectionStats, useDeleteDocument, useBulkDeleteDocuments } from "@/hooks/useDocuments";
import { useToast } from "@/hooks/use-toast";
import { exportDocuments } from "@/lib/api/documents";

export function DocumentList() {
  const { data: stats, isLoading } = useCollectionStats();
  const { mutate: deleteDocument } = useDeleteDocument();
  const { mutate: bulkDelete } = useBulkDeleteDocuments();
  const { toast } = useToast();

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [documents, setDocuments] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const loadDocuments = async () => {
    setLoadingDocs(true);
    try {
      const response = await exportDocuments(100);
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

  const toggleSelectAll = () => {
    if (selectedIds.length === filteredDocuments.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredDocuments.map((doc) => doc.id));
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    if (!searchQuery) return true;
    const search = searchQuery.toLowerCase();
    return (
      doc.metadata?.endpoint?.toLowerCase().includes(search) ||
      doc.metadata?.api_name?.toLowerCase().includes(search) ||
      doc.metadata?.method?.toLowerCase().includes(search) ||
      doc.content?.toLowerCase().includes(search)
    );
  });

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

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Document Library</CardTitle>
              <CardDescription>
                {isLoading ? "Loading..." : `${stats?.total_documents || 0} documents indexed`}
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
            <div className="flex items-center space-x-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
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
          </CardContent>
        </Card>
      )}

      {/* Document List */}
      {documents.length > 0 ? (
        <Card>
          <CardContent className="p-0">
            {/* Select All */}
            <div className="flex items-center space-x-3 p-4 border-b bg-muted/30">
              <Checkbox
                checked={selectedIds.length === filteredDocuments.length && filteredDocuments.length > 0}
                onCheckedChange={toggleSelectAll}
              />
              <span className="text-sm font-medium">
                {selectedIds.length > 0
                  ? `${selectedIds.length} selected`
                  : "Select all"}
              </span>
            </div>

            {/* Document Items */}
            <div className="divide-y">
              {filteredDocuments.map((doc) => {
                const SourceIcon = getSourceIcon(doc.metadata?.source || "");
                return (
                  <div
                    key={doc.id}
                    className="flex items-center space-x-3 p-4 hover:bg-muted/50 transition-colors"
                  >
                    <Checkbox
                      checked={selectedIds.includes(doc.id)}
                      onCheckedChange={() => toggleSelection(doc.id)}
                    />

                    <SourceIcon className="h-5 w-5 text-muted-foreground flex-shrink-0" />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <p className="text-sm font-medium truncate">
                          {doc.metadata?.endpoint || doc.metadata?.path || "Untitled"}
                        </p>
                        {doc.metadata?.method && (
                          <Badge variant="outline" className="text-xs">
                            {doc.metadata.method}
                          </Badge>
                        )}
                        {doc.metadata?.source && (
                          <Badge variant="secondary" className="text-xs">
                            {doc.metadata.source}
                          </Badge>
                        )}
                      </div>
                      {doc.metadata?.api_name && (
                        <p className="text-xs text-muted-foreground">
                          {doc.metadata.api_name}
                        </p>
                      )}
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(doc.id)}
                      className="flex-shrink-0"
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                );
              })}
            </div>

            {filteredDocuments.length === 0 && (
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
    </div>
  );
}
