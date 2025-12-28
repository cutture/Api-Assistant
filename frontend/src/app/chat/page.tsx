/**
 * Chat page - Interactive chat interface
 * Week 5 implementation
 */

import { MainLayout } from "@/components/layout/MainLayout";

export default function ChatPage() {
  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chat Assistant</h1>
          <p className="text-muted-foreground mt-2">
            Ask questions about your APIs
          </p>
        </div>

        <div className="border-2 border-dashed rounded-lg p-12 text-center">
          <p className="text-muted-foreground">
            Chat interface coming in Week 5
          </p>
        </div>
      </div>
    </MainLayout>
  );
}
