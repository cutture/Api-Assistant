/**
 * Chat page - Interactive chat interface
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { useToast } from "@/hooks/use-toast";
import { search } from "@/lib/api/search";

export default function ChatPage() {
  const { toast } = useToast();

  const handleSendMessage = async (message: string): Promise<string> => {
    try {
      // Use advanced search to find relevant context
      const response = await search({
        query: message,
        n_results: 3,
        mode: "reranked",
        use_query_expansion: true,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      // Format response with relevant API information
      const results = response.data?.results || [];

      if (results.length === 0) {
        return "I couldn't find any relevant API documentation for your question. Please try rephrasing or ensure you have indexed API specifications.";
      }

      // Build response with top results
      let responseText = "Based on your indexed APIs, here's what I found:\n\n";

      results.forEach((result, index) => {
        const metadata = result.metadata;
        responseText += `### ${index + 1}. ${metadata.endpoint || metadata.path || "Endpoint"}\n`;

        if (metadata.method) {
          responseText += `**Method:** ${metadata.method}\n`;
        }

        if (metadata.api_name) {
          responseText += `**API:** ${metadata.api_name}\n`;
        }

        if (metadata.description) {
          responseText += `**Description:** ${metadata.description}\n`;
        }

        if (result.content) {
          responseText += `\n\`\`\`json\n${result.content.slice(0, 300)}\n\`\`\`\n`;
        }

        responseText += `\n**Relevance Score:** ${(result.score * 100).toFixed(1)}%\n\n`;
      });

      return responseText;
    } catch (error: any) {
      toast({
        title: "Search Error",
        description: error.message || "Failed to search APIs",
        variant: "destructive",
      });
      throw error;
    }
  };

  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chat Assistant</h1>
          <p className="text-muted-foreground mt-2">
            Ask questions about your APIs and get instant answers
          </p>
        </div>

        <ChatInterface onSendMessage={handleSendMessage} />
      </div>
    </MainLayout>
  );
}
