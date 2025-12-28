/**
 * Search page - Advanced search interface
 * Week 2 implementation
 */

import { MainLayout } from "@/components/layout/MainLayout";

export default function SearchPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Search</h1>
          <p className="text-muted-foreground mt-2">
            Search through your indexed API documentation
          </p>
        </div>

        <div className="border-2 border-dashed rounded-lg p-12 text-center">
          <p className="text-muted-foreground">
            Search interface coming in Week 2
          </p>
        </div>
      </div>
    </MainLayout>
  );
}
