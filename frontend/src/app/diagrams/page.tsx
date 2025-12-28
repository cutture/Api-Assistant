/**
 * Diagrams page - Generate Mermaid diagrams from API documentation
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { DiagramGenerator } from "@/components/diagrams/DiagramGenerator";

export default function DiagramsPage() {
  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Diagram Generator</h1>
          <p className="text-muted-foreground mt-2">
            Generate sequence diagrams, authentication flows, and more from your indexed APIs
          </p>
        </div>

        <DiagramGenerator />
      </div>
    </MainLayout>
  );
}
