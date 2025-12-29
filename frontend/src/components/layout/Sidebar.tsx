/**
 * Sidebar component for quick stats and actions
 */

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCollectionStats } from "@/hooks/useDocuments";
import { FileText, Database, Layers } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function Sidebar() {
  const { data: stats, isLoading } = useCollectionStats();

  return (
    <aside className="w-64 border-r bg-muted/20 p-4">
      <div className="space-y-4">
        {/* Collection Stats */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span>Collection Stats</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <Skeleton className="h-10 w-full" />
            ) : (
              <>
                <StatItem
                  icon={FileText}
                  label="Total Documents"
                  value={stats?.collection?.total_documents || 0}
                />
              </>
            )}
          </CardContent>
        </Card>

        {/* Quick Info */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Quick Info</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <p>Upload API specs to get started</p>
            <p>Supports OpenAPI, GraphQL, and Postman collections</p>
          </CardContent>
        </Card>
      </div>
    </aside>
  );
}

interface StatItemProps {
  icon: React.ElementType;
  label: string;
  value: number;
}

function StatItem({ icon: Icon, label, value }: StatItemProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
        <Icon className="h-3 w-3" />
        <span>{label}</span>
      </div>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}
