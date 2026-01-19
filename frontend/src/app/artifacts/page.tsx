/**
 * Artifacts Page
 *
 * Page for managing uploaded and generated artifacts.
 */

"use client";

import { useState } from "react";
import { ArtifactList, ArtifactUpload } from "@/components/artifacts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileUp, Files, FolderArchive } from "lucide-react";

export default function ArtifactsPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadComplete = () => {
    // Refresh the artifact list when upload completes
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <FolderArchive className="h-8 w-8" />
          <h1 className="text-3xl font-bold">Artifacts</h1>
        </div>
        <p className="text-muted-foreground">
          Manage your uploaded code files, generated outputs, and downloadable bundles.
        </p>
      </div>

      <Tabs defaultValue="browse" className="space-y-6">
        <TabsList>
          <TabsTrigger value="browse" className="gap-2">
            <Files className="h-4 w-4" />
            Browse
          </TabsTrigger>
          <TabsTrigger value="upload" className="gap-2">
            <FileUp className="h-4 w-4" />
            Upload
          </TabsTrigger>
        </TabsList>

        <TabsContent value="browse">
          <ArtifactList key={refreshKey} />
        </TabsContent>

        <TabsContent value="upload">
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <h2 className="text-xl font-semibold mb-4">Upload Files</h2>
              <ArtifactUpload
                onUploadComplete={handleUploadComplete}
                onUploadError={(error) => console.error("Upload error:", error)}
              />
            </div>
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Supported File Types</h2>
              <div className="space-y-3 text-sm">
                <div>
                  <h3 className="font-medium">Code Files</h3>
                  <p className="text-muted-foreground">
                    Python (.py), JavaScript (.js), TypeScript (.ts, .tsx), Java (.java), Go (.go), C# (.cs)
                  </p>
                </div>
                <div>
                  <h3 className="font-medium">Configuration</h3>
                  <p className="text-muted-foreground">
                    JSON (.json), YAML (.yaml, .yml)
                  </p>
                </div>
                <div>
                  <h3 className="font-medium">Documentation</h3>
                  <p className="text-muted-foreground">
                    Markdown (.md), Text (.txt)
                  </p>
                </div>
              </div>
              <div className="border-t pt-4 mt-4">
                <h3 className="font-medium mb-2">Usage Tips</h3>
                <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                  <li>Upload code files to provide context for code generation</li>
                  <li>Generated code is automatically saved as artifacts</li>
                  <li>Download ZIP bundles for complete project outputs</li>
                  <li>Artifacts expire after 30 days by default</li>
                </ul>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
