/**
 * Diagram generator component - Generate diagrams from API endpoints
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useGenerateSequenceDiagram, useGenerateAuthFlowDiagram } from "@/hooks/useDiagrams";
import { MermaidViewer } from "./MermaidViewer";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { DiagramResponse } from "@/types";

export function DiagramGenerator() {
  const [diagramType, setDiagramType] = useState<"sequence" | "auth">("sequence");
  const [endpointId, setEndpointId] = useState("");
  const [authType, setAuthType] = useState<"bearer" | "oauth2" | "apikey" | "basic">("bearer");
  const [generatedDiagram, setGeneratedDiagram] = useState<DiagramResponse | null>(null);

  const { mutate: generateSequence, isPending: isGeneratingSequence } = useGenerateSequenceDiagram();
  const { mutate: generateAuth, isPending: isGeneratingAuth } = useGenerateAuthFlowDiagram();
  const { toast } = useToast();

  const isGenerating = isGeneratingSequence || isGeneratingAuth;

  const handleGenerate = () => {
    if (diagramType === "sequence") {
      if (!endpointId.trim()) {
        toast({
          title: "Endpoint ID required",
          description: "Please enter an endpoint document ID",
          variant: "destructive",
        });
        return;
      }

      generateSequence(
        { endpoint_id: endpointId },
        {
          onSuccess: (data) => {
            setGeneratedDiagram(data || null);
            toast({
              title: "Diagram generated",
              description: "Sequence diagram created successfully",
            });
          },
          onError: (error: any) => {
            toast({
              title: "Generation failed",
              description: error.message || "Failed to generate diagram",
              variant: "destructive",
            });
          },
        }
      );
    } else {
      generateAuth(
        { auth_type: authType },
        {
          onSuccess: (data) => {
            setGeneratedDiagram(data || null);
            toast({
              title: "Diagram generated",
              description: "Authentication flow diagram created successfully",
            });
          },
          onError: (error: any) => {
            toast({
              title: "Generation failed",
              description: error.message || "Failed to generate diagram",
              variant: "destructive",
            });
          },
        }
      );
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Generate Diagram</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Diagram Type Selection */}
          <div className="space-y-2">
            <Label htmlFor="diagram-type">Diagram Type</Label>
            <Select value={diagramType} onValueChange={(v) => setDiagramType(v as any)}>
              <SelectTrigger id="diagram-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sequence">Sequence Diagram</SelectItem>
                <SelectItem value="auth">Authentication Flow</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Sequence Diagram Options */}
          {diagramType === "sequence" && (
            <div className="space-y-2">
              <Label htmlFor="endpoint-id">Endpoint Document ID</Label>
              <Input
                id="endpoint-id"
                placeholder="Enter document ID from search results"
                value={endpointId}
                onChange={(e) => setEndpointId(e.target.value)}
              />
              <p className="text-sm text-muted-foreground">
                Search for an endpoint and copy its document ID to generate a sequence diagram
              </p>
            </div>
          )}

          {/* Auth Flow Options */}
          {diagramType === "auth" && (
            <div className="space-y-2">
              <Label htmlFor="auth-type">Authentication Type</Label>
              <Select value={authType} onValueChange={(v) => setAuthType(v as any)}>
                <SelectTrigger id="auth-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bearer">Bearer Token</SelectItem>
                  <SelectItem value="oauth2">OAuth 2.0</SelectItem>
                  <SelectItem value="apikey">API Key</SelectItem>
                  <SelectItem value="basic">Basic Auth</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Generate Button */}
          <Button onClick={handleGenerate} disabled={isGenerating} className="w-full">
            {isGenerating && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Generate Diagram
          </Button>
        </CardContent>
      </Card>

      {/* Generated Diagram Display */}
      {generatedDiagram && (
        <MermaidViewer
          code={generatedDiagram.mermaid_code}
          title={generatedDiagram.title || `${generatedDiagram.diagram_type} Diagram`}
        />
      )}
    </div>
  );
}
