/**
 * Diagram generator component - Generate diagrams from API endpoints
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  useGenerateSequenceDiagram,
  useGenerateAuthFlowDiagram,
  useGenerateERDiagram,
  useGenerateOverviewDiagram,
} from "@/hooks/useDiagrams";
import { MermaidViewer } from "./MermaidViewer";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { DiagramResponse } from "@/types";

type DiagramTypeValue = "sequence" | "auth" | "er" | "overview";

export function DiagramGenerator() {
  const [diagramType, setDiagramType] = useState<DiagramTypeValue>("sequence");

  // Sequence diagram state
  const [endpointId, setEndpointId] = useState("");

  // Auth flow state
  const [authType, setAuthType] = useState<"bearer" | "oauth2" | "apikey" | "basic">("bearer");

  // ER diagram state
  const [schemaContent, setSchemaContent] = useState("");

  // Overview diagram state
  const [apiTitle, setApiTitle] = useState("");
  const [endpointsJson, setEndpointsJson] = useState("[\n  {\n    \"path\": \"/users\",\n    \"method\": \"GET\",\n    \"tags\": [\"Users\"]\n  }\n]");

  const [generatedDiagram, setGeneratedDiagram] = useState<DiagramResponse | null>(null);

  const { mutate: generateSequence, isPending: isGeneratingSequence } = useGenerateSequenceDiagram();
  const { mutate: generateAuth, isPending: isGeneratingAuth } = useGenerateAuthFlowDiagram();
  const { mutate: generateER, isPending: isGeneratingER } = useGenerateERDiagram();
  const { mutate: generateOverview, isPending: isGeneratingOverview } = useGenerateOverviewDiagram();
  const { toast } = useToast();

  const isGenerating = isGeneratingSequence || isGeneratingAuth || isGeneratingER || isGeneratingOverview;

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
    } else if (diagramType === "auth") {
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
    } else if (diagramType === "er") {
      if (!schemaContent.trim()) {
        toast({
          title: "Schema required",
          description: "Please enter a GraphQL schema",
          variant: "destructive",
        });
        return;
      }

      generateER(
        { schema_content: schemaContent },
        {
          onSuccess: (data) => {
            setGeneratedDiagram(data || null);
            toast({
              title: "Diagram generated",
              description: "Entity-Relationship diagram created successfully",
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
    } else if (diagramType === "overview") {
      if (!apiTitle.trim()) {
        toast({
          title: "API title required",
          description: "Please enter an API title",
          variant: "destructive",
        });
        return;
      }

      try {
        const endpoints = JSON.parse(endpointsJson);
        if (!Array.isArray(endpoints)) {
          throw new Error("Endpoints must be an array");
        }

        generateOverview(
          { api_title: apiTitle, endpoints },
          {
            onSuccess: (data) => {
              setGeneratedDiagram(data || null);
              toast({
                title: "Diagram generated",
                description: "API overview diagram created successfully",
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
      } catch (e) {
        toast({
          title: "Invalid JSON",
          description: "Please enter valid JSON for endpoints",
          variant: "destructive",
        });
      }
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
            <Select value={diagramType} onValueChange={(v) => setDiagramType(v as DiagramTypeValue)}>
              <SelectTrigger id="diagram-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sequence">Sequence Diagram</SelectItem>
                <SelectItem value="auth">Authentication Flow</SelectItem>
                <SelectItem value="er">Entity-Relationship Diagram</SelectItem>
                <SelectItem value="overview">API Overview</SelectItem>
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

          {/* ER Diagram Options */}
          {diagramType === "er" && (
            <div className="space-y-2">
              <Label htmlFor="schema-content">GraphQL Schema</Label>
              <Textarea
                id="schema-content"
                placeholder="Paste your GraphQL schema here..."
                value={schemaContent}
                onChange={(e) => setSchemaContent(e.target.value)}
                rows={10}
                className="font-mono text-sm"
              />
              <p className="text-sm text-muted-foreground">
                Enter a GraphQL schema to generate an Entity-Relationship diagram
              </p>
            </div>
          )}

          {/* Overview Diagram Options */}
          {diagramType === "overview" && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="api-title">API Title</Label>
                <Input
                  id="api-title"
                  placeholder="e.g., User Management API"
                  value={apiTitle}
                  onChange={(e) => setApiTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="endpoints-json">Endpoints (JSON)</Label>
                <Textarea
                  id="endpoints-json"
                  placeholder="Enter endpoints as JSON array..."
                  value={endpointsJson}
                  onChange={(e) => setEndpointsJson(e.target.value)}
                  rows={10}
                  className="font-mono text-sm"
                />
                <p className="text-sm text-muted-foreground">
                  Enter endpoints as JSON array with path, method, and tags
                </p>
              </div>
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
