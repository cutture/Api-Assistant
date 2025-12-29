/**
 * Collection statistics card component
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCollectionStats } from "@/hooks/useDocuments";
import { Skeleton } from "@/components/ui/skeleton";
import { Database, FileText, Globe, Code } from "lucide-react";

export function StatsCard() {
  const { data: stats, isLoading, error } = useCollectionStats();

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Collection Statistics</CardTitle>
          <CardDescription className="text-destructive">
            Failed to load statistics
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Database className="h-5 w-5" />
          <span>Collection Statistics</span>
        </CardTitle>
        <CardDescription>
          Overview of indexed API documentation
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <StatItem
              icon={FileText}
              label="Total Documents"
              value={stats?.collection?.total_documents || 0}
              color="blue"
            />
            <StatItem
              icon={Database}
              label="Collection"
              value={stats?.collection?.collection_name || "default"}
              color="green"
              isText
            />
          </div>
        )}

        {/* Features */}
        {stats?.features && (
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-medium mb-3">Enabled Features</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {Object.entries(stats.features).map(([feature, enabled]) => (
                <div
                  key={feature}
                  className={`px-3 py-2 rounded-md text-center ${
                    enabled ? "bg-green-100 dark:bg-green-900/20" : "bg-muted"
                  }`}
                >
                  <div className="text-xs capitalize">
                    {feature.replace(/_/g, " ")}
                  </div>
                  <div className="text-sm font-semibold">
                    {enabled ? "✓" : "✗"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface StatItemProps {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: "blue" | "green" | "purple" | "orange";
  isText?: boolean;
}

function StatItem({ icon: Icon, label, value, color, isText = false }: StatItemProps) {
  const colorClasses = {
    blue: "bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
    green: "bg-green-100 text-green-600 dark:bg-green-900/20 dark:text-green-400",
    purple: "bg-purple-100 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400",
    orange: "bg-orange-100 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400",
  };

  return (
    <div className="flex flex-col space-y-2 p-4 border rounded-lg">
      <div className={`inline-flex h-8 w-8 items-center justify-center rounded-lg ${colorClasses[color]}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className={isText ? "text-lg font-bold truncate" : "text-2xl font-bold"}>{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
