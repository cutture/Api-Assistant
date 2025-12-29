/**
 * Mermaid diagram viewer component
 */

"use client";

import { useEffect, useRef, useState } from "react";
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
  const [isRendering, setIsRendering] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !code) return;

      try {
        setIsRendering(true);

        // Initialize Mermaid
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
          fontFamily: "arial, sans-serif",
        });

        // Clear previous content
        containerRef.current.innerHTML = "";

        // Generate a unique ID for this diagram
        const id = `mermaid-${Date.now()}`;

        // Render the diagram
        const { svg } = await mermaid.render(id, code);

        // Insert the rendered SVG
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (error: any) {
        console.error("Mermaid rendering error:", error);
        if (containerRef.current) {
          containerRef.current.innerHTML = `
            <div class="text-destructive p-4">
              <p class="font-semibold">Failed to render diagram</p>
              <p class="text-sm mt-1">${error.message || "Invalid Mermaid syntax"}</p>
            </div>
          `;
        }
        toast({
          title: "Rendering failed",
          description: error.message || "Failed to render diagram",
          variant: "destructive",
        });
      } finally {
        setIsRendering(false);
      }
    };

    renderDiagram();
  }, [code, toast]);

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
          description: "No diagram found to download. Please wait for the diagram to render.",
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
      a.download = `${title?.replace(/\s+/g, "-") || "diagram"}.svg`;
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
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadSVG}
                disabled={isRendering}
              >
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
          className="mermaid flex justify-center items-center p-4 bg-background rounded-md min-h-[200px]"
        >
          {isRendering && (
            <div className="text-muted-foreground">
              Rendering diagram...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
