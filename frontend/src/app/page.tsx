/**
 * Home page - Document Management
 */

import { MainLayout } from "@/components/layout/MainLayout";
import { DocumentUploader } from "@/components/documents/DocumentUploader";
import { StatsCard } from "@/components/documents/StatsCard";

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
        <DocumentUploader />
      </div>
    </MainLayout>
  );
}
