/**
 * Document details modal with editing capabilities
 */

"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2, Edit2, Save, X, FileText, Globe, Code } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface DocumentDetailsModalProps {
  document: any;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDelete: (documentId: string) => void;
  onUpdate?: (documentId: string, metadata: any) => void;
}

export function DocumentDetailsModal({
  document,
  open,
  onOpenChange,
  onDelete,
  onUpdate,
}: DocumentDetailsModalProps) {
  const { toast } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [editedMetadata, setEditedMetadata] = useState<any>({});

  if (!document) return null;

  const handleEdit = () => {
    setEditedMetadata({ ...document.metadata });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditedMetadata({});
    setIsEditing(false);
  };

  const handleSaveEdit = () => {
    if (onUpdate) {
      onUpdate(document.id, editedMetadata);
      toast({
        title: "Metadata updated",
        description: "Document metadata has been updated successfully",
      });
    }
    setIsEditing(false);
  };

  const handleDelete = () => {
    onDelete(document.id);
    onOpenChange(false);
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

  const SourceIcon = getSourceIcon(document.metadata?.source || "");

  const formatSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
  };

  const getDocumentName = (): string => {
    return (
      document.metadata?.endpoint ||
      document.metadata?.path ||
      document.metadata?.api_title ||
      document.metadata?.source_file ||
      "Untitled"
    );
  };

  const renderMetadataField = (key: string, value: any) => {
    if (isEditing && ["endpoint", "path", "api_title", "api_name", "method", "description", "summary"].includes(key)) {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-sm font-medium capitalize">
            {key.replace(/_/g, " ")}
          </Label>
          <Input
            id={key}
            value={editedMetadata[key] || ""}
            onChange={(e) =>
              setEditedMetadata({ ...editedMetadata, [key]: e.target.value })
            }
            className="text-sm"
          />
        </div>
      );
    }

    return (
      <div key={key} className="space-y-1">
        <p className="text-sm font-medium text-muted-foreground capitalize">
          {key.replace(/_/g, " ")}
        </p>
        <p className="text-sm">
          {typeof value === "object" ? JSON.stringify(value, null, 2) : String(value)}
        </p>
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <SourceIcon className="h-6 w-6 text-muted-foreground" />
              <div>
                <DialogTitle className="text-xl">{getDocumentName()}</DialogTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="secondary" className="text-xs">
                    {document.metadata?.source || "unknown"}
                  </Badge>
                  {document.metadata?.method && (
                    <Badge variant="outline" className="text-xs">
                      {document.metadata.method}
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {!isEditing ? (
                <>
                  <Button variant="outline" size="sm" onClick={handleEdit}>
                    <Edit2 className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                  <Button variant="destructive" size="sm" onClick={handleDelete}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="outline" size="sm" onClick={handleCancelEdit}>
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                  <Button variant="default" size="sm" onClick={handleSaveEdit}>
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                </>
              )}
            </div>
          </div>
        </DialogHeader>

        <Tabs defaultValue="overview" className="flex-1 overflow-hidden">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 mt-4">
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Document ID</p>
                    <p className="text-sm font-mono break-all">{document.id}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Content Size</p>
                    <p className="text-sm">{formatSize(document.content?.length || 0)}</p>
                  </div>
                </div>

                {document.metadata?.api_name && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">API Name</p>
                    <p className="text-sm">{document.metadata.api_name}</p>
                  </div>
                )}

                {document.metadata?.description && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Description</p>
                    <p className="text-sm">{document.metadata.description}</p>
                  </div>
                )}

                {document.metadata?.summary && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-muted-foreground">Summary</p>
                    <p className="text-sm">{document.metadata.summary}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {document.metadata?.chunk_index !== undefined && (
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-muted-foreground">Chunk Index</p>
                      <p className="text-sm">{document.metadata.chunk_index}</p>
                    </div>
                  )}
                  {document.metadata?.total_chunks !== undefined && (
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-muted-foreground">Total Chunks</p>
                      <p className="text-sm">{document.metadata.total_chunks}</p>
                    </div>
                  )}
                </div>

                {document.metadata?.tags && document.metadata.tags.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Tags</p>
                    <div className="flex flex-wrap gap-2">
                      {document.metadata.tags.map((tag: string, index: number) => (
                        <Badge key={index} variant="outline">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="content" className="mt-4">
            <ScrollArea className="h-[400px] pr-4">
              <div className="bg-muted/30 rounded-lg p-4">
                <pre className="text-xs whitespace-pre-wrap font-mono">
                  {document.content}
                </pre>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="metadata" className="mt-4">
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-4">
                {isEditing && (
                  <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      Editing mode: Modify the editable fields below and click Save to update.
                    </p>
                  </div>
                )}
                {Object.entries(document.metadata || {}).map(([key, value]) =>
                  renderMetadataField(key, value)
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
