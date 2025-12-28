/**
 * Mermaid diagram viewer component
 */

"use client";

import { useEffect, useRef } from "react";
import mermaid from "mermaid";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Copy } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export interface MermaidViewerProps {
  code: string;
  title?: string;
}

export function MermaidViewer({ code, title }: MermaidViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: "default",
      securityLevel: "loose",
    });

    if (containerRef.current) {
      containerRef.current.innerHTML = code;
      mermaid.contentLoaded();
    }
  }, [code]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    toast({
      title: "Code copied",
      description: "Mermaid code copied to clipboard",
    });
  };

  const handleDownloadSVG = async () => {
    try {
      // Get the SVG element
      const svgElement = containerRef.current?.querySelector("svg");
      if (!svgElement) {
        toast({
          title: "Error",
          description: "No diagram found to download",
          variant: "destructive",
        });
        return;
      }

      // Serialize SVG to string
      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(svgElement);

      // Create blob and download
      const blob = new Blob([svgString], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${title || "diagram"}.svg`;
      a.click();
      URL.revokeObjectURL(url);

      toast({
        title: "Download started",
        description: "Diagram downloaded as SVG",
      });
    } catch (error: any) {
      toast({
        title: "Download failed",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  return (
    <Card>
      {title && (
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">{title}</CardTitle>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={handleCopyCode}>
                <Copy className="h-4 w-4 mr-2" />
                Copy Code
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownloadSVG}>
                <Download className="h-4 w-4 mr-2" />
                Download SVG
              </Button>
            </div>
          </div>
        </CardHeader>
      )}
      <CardContent>
        <div
          ref={containerRef}
          className="mermaid flex justify-center items-center p-4 bg-background rounded-md"
        />
      </CardContent>
    </Card>
  );
}
