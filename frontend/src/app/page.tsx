/**
 * Home page - Document Management
 */

import { MainLayout } from "@/components/layout/MainLayout";
import { DocumentUploader } from "@/components/documents/DocumentUploader";
import { StatsCard } from "@/components/documents/StatsCard";
import { DocumentList } from "@/components/documents/DocumentList";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Home() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Document Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Upload and manage your API documentation
          </p>
        </div>

        <StatsCard />

        <Tabs defaultValue="upload" className="space-y-4">
          <TabsList>
            <TabsTrigger value="upload">Upload Documents</TabsTrigger>
            <TabsTrigger value="library">Document Library</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <DocumentUploader />
          </TabsContent>

          <TabsContent value="library" className="space-y-4">
            <DocumentList />
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
}
