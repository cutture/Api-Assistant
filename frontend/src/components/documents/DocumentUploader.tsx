/**
 * Document uploader with drag & drop support
 */

"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useUploadDocuments } from "@/hooks/useDocuments";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type FileFormat = "openapi" | "graphql" | "postman";

export function DocumentUploader() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [format, setFormat] = useState<FileFormat | undefined>();

  const { mutate: upload, isPending } = useUploadDocuments();
  const { toast } = useToast();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    setSelectedFiles(files);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setSelectedFiles(files);
    }
  }, []);

  const handleUpload = useCallback(() => {
    if (selectedFiles.length === 0) {
      toast({
        title: "No files selected",
        description: "Please select at least one file to upload",
        variant: "destructive",
      });
      return;
    }

    upload(
      { files: selectedFiles, format },
      {
        onSuccess: (data) => {
          const newCount = data?.new_count || 0;
          const skippedCount = data?.skipped_count || 0;

          let description = `Successfully indexed ${newCount} new document${newCount !== 1 ? 's' : ''}`;
          if (skippedCount > 0) {
            description += ` (${skippedCount} duplicate${skippedCount !== 1 ? 's' : ''} skipped)`;
          }

          toast({
            title: "Upload successful",
            description,
          });
          setSelectedFiles([]);
          setFormat(undefined);
        },
        onError: (error: any) => {
          toast({
            title: "Upload failed",
            description: error.message || "Failed to upload documents",
            variant: "destructive",
          });
        },
      }
    );
  }, [selectedFiles, format, upload, toast]);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles((files) => files.filter((_, i) => i !== index));
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload API Documentation</CardTitle>
        <CardDescription>
          Upload OpenAPI, GraphQL, or Postman collection files
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drag & Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-muted-foreground/50"
          )}
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground mb-2">
            Drag and drop files here, or click to browse
          </p>
          <input
            type="file"
            multiple
            accept=".yaml,.yml,.json,.graphql,.gql"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <Label htmlFor="file-upload">
            <Button variant="outline" size="sm" asChild>
              <span>Browse Files</span>
            </Button>
          </Label>
        </div>

        {/* Format Selection */}
        <div className="space-y-2">
          <Label>File Format (Optional - Auto-detect if not specified)</Label>
          <div className="flex space-x-2">
            <Button
              variant={format === "openapi" ? "default" : "outline"}
              size="sm"
              onClick={() => setFormat(format === "openapi" ? undefined : "openapi")}
            >
              OpenAPI
            </Button>
            <Button
              variant={format === "graphql" ? "default" : "outline"}
              size="sm"
              onClick={() => setFormat(format === "graphql" ? undefined : "graphql")}
            >
              GraphQL
            </Button>
            <Button
              variant={format === "postman" ? "default" : "outline"}
              size="sm"
              onClick={() => setFormat(format === "postman" ? undefined : "postman")}
            >
              Postman
            </Button>
          </div>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="space-y-2">
            <Label>Selected Files ({selectedFiles.length})</Label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-muted rounded-md"
                >
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    disabled={isPending}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Button */}
        <div className="flex justify-end">
          <Button
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || isPending}
          >
            {isPending ? (
              <>
                <Upload className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload & Index
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
