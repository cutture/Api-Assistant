/**
 * ArtifactUpload Component
 *
 * Drag-and-drop file upload component for artifacts.
 */

"use client";

import { useState, useCallback, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Upload,
  X,
  File,
  FileCode,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadArtifact, UploadResponse, formatFileSize } from "@/lib/api/artifacts";

interface UploadFile {
  file: File;
  id: string;
  status: "pending" | "uploading" | "success" | "error";
  progress: number;
  response?: UploadResponse;
  error?: string;
}

interface ArtifactUploadProps {
  sessionId?: string;
  onUploadComplete?: (response: UploadResponse) => void;
  onUploadError?: (error: string) => void;
  className?: string;
  maxFileSize?: number; // in MB
  acceptedTypes?: string[];
}

export function ArtifactUpload({
  sessionId,
  onUploadComplete,
  onUploadError,
  className,
  maxFileSize = 50,
  acceptedTypes = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".cs", ".json", ".yaml", ".yml", ".md", ".txt"],
}: ArtifactUploadProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [artifactType, setArtifactType] = useState("uploaded");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const filesToAdd: UploadFile[] = [];

    for (const file of Array.from(newFiles)) {
      // Check file size
      if (file.size > maxFileSize * 1024 * 1024) {
        onUploadError?.(`File "${file.name}" exceeds maximum size of ${maxFileSize}MB`);
        continue;
      }

      filesToAdd.push({
        file,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        status: "pending",
        progress: 0,
      });
    }

    setFiles((prev) => [...prev, ...filesToAdd]);
  }, [maxFileSize, onUploadError]);

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const uploadFile = useCallback(async (uploadFile: UploadFile) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: "uploading", progress: 0 } : f
      )
    );

    try {
      const response = await uploadArtifact(uploadFile.file, {
        artifact_type: artifactType,
        session_id: sessionId,
      });

      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: "success", progress: 100, response }
            : f
        )
      );

      onUploadComplete?.(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed";

      setFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: "error", error: errorMessage }
            : f
        )
      );

      onUploadError?.(errorMessage);
    }
  }, [artifactType, sessionId, onUploadComplete, onUploadError]);

  const uploadAll = useCallback(async () => {
    const pendingFiles = files.filter((f) => f.status === "pending");

    for (const file of pendingFiles) {
      await uploadFile(file);
    }
  }, [files, uploadFile]);

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

    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  }, [addFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
    // Reset input
    e.target.value = "";
  }, [addFiles]);

  const getFileIcon = (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext && [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".cs"].some(e => e.endsWith(ext))) {
      return <FileCode className="h-5 w-5" />;
    }
    return <File className="h-5 w-5" />;
  };

  const getStatusIcon = (status: UploadFile["status"]) => {
    switch (status) {
      case "uploading":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case "success":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const uploadingCount = files.filter((f) => f.status === "uploading").length;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Upload type selector */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">Upload as:</span>
        <Select value={artifactType} onValueChange={setArtifactType}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="uploaded">Uploaded File</SelectItem>
            <SelectItem value="generated">Generated Code</SelectItem>
            <SelectItem value="output">Output</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Drop zone */}
      <Card
        className={cn(
          "border-2 border-dashed transition-colors cursor-pointer",
          isDragging && "border-primary bg-primary/5",
          !isDragging && "border-muted-foreground/25 hover:border-primary/50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <CardContent className="flex flex-col items-center justify-center py-8">
          <Upload className={cn("h-10 w-10 mb-4", isDragging ? "text-primary" : "text-muted-foreground")} />
          <p className="text-center text-muted-foreground">
            <span className="font-medium text-foreground">Click to upload</span>
            {" "}or drag and drop
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Max file size: {maxFileSize}MB
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={acceptedTypes.join(",")}
            onChange={handleFileSelect}
            className="hidden"
          />
        </CardContent>
      </Card>

      {/* File list */}
      {files.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {files.map((uploadFile) => (
                <div
                  key={uploadFile.id}
                  className="flex items-center gap-3 p-3"
                >
                  <div className="text-muted-foreground">
                    {getFileIcon(uploadFile.file)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">
                        {uploadFile.file.name}
                      </span>
                      {getStatusIcon(uploadFile.status)}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{formatFileSize(uploadFile.file.size)}</span>
                      {uploadFile.error && (
                        <span className="text-red-500">{uploadFile.error}</span>
                      )}
                    </div>
                    {uploadFile.status === "uploading" && (
                      <Progress value={uploadFile.progress} className="h-1 mt-1" />
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(uploadFile.id)}
                    disabled={uploadFile.status === "uploading"}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload button */}
      {pendingCount > 0 && (
        <Button
          onClick={uploadAll}
          disabled={uploadingCount > 0}
          className="w-full"
        >
          {uploadingCount > 0 ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              Upload {pendingCount} file{pendingCount > 1 ? "s" : ""}
            </>
          )}
        </Button>
      )}
    </div>
  );
}

export default ArtifactUpload;
