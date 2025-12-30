/**
 * Chat input component
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Paperclip, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

interface ChatInputProps {
  onSend: (message: string, files?: File[]) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  isLoading,
  placeholder = "Ask a question about your APIs...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((message.trim() || attachedFiles.length > 0) && !isLoading) {
      onSend(message.trim(), attachedFiles.length > 0 ? attachedFiles : undefined);
      setMessage("");
      setAttachedFiles([]);
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setAttachedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setAttachedFiles((files) => files.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <form onSubmit={handleSubmit} className="border-t bg-background p-4">
      {/* Attached Files Display */}
      {attachedFiles.length > 0 && (
        <div className="mb-3 space-y-2">
          <Label className="text-xs text-muted-foreground">
            Attached Files ({attachedFiles.length})
          </Label>
          <div className="flex flex-wrap gap-2">
            {attachedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-md text-sm"
              >
                <Paperclip className="h-3 w-3" />
                <span className="max-w-[200px] truncate">{file.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="ml-1 text-muted-foreground hover:text-foreground"
                  disabled={isLoading}
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end space-x-2">
        <div className="flex-1 flex items-end space-x-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.md,.markdown,.json,.yaml,.yml,.graphql,.gql"
            onChange={handleFileSelect}
            className="hidden"
            id="chat-file-upload"
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="h-[60px] w-[60px] shrink-0"
            title="Attach files"
          >
            <Paperclip className="h-5 w-5" />
          </Button>
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            className="min-h-[60px] max-h-[200px] resize-none"
            rows={1}
          />
        </div>
        <Button
          type="submit"
          size="icon"
          disabled={(!message.trim() && attachedFiles.length === 0) || isLoading}
          className="h-[60px] w-[60px] shrink-0"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        Press Enter to send, Shift+Enter for new line • Attach PDFs, text files, API specs
      </p>
    </form>
  );
}
