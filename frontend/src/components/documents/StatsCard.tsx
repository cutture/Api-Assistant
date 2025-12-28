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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatItem
              icon={FileText}
              label="Total Documents"
              value={stats?.total_documents || 0}
              color="blue"
            />
            <StatItem
              icon={Globe}
              label="OpenAPI"
              value={stats?.sources?.openapi || 0}
              color="green"
            />
            <StatItem
              icon={Code}
              label="GraphQL"
              value={stats?.sources?.graphql || 0}
              color="purple"
            />
            <StatItem
              icon={FileText}
              label="Postman"
              value={stats?.sources?.postman || 0}
              color="orange"
            />
          </div>
        )}

        {/* HTTP Methods Breakdown */}
        {stats && stats.methods && Object.keys(stats.methods).length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-medium mb-3">HTTP Methods</h4>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
              {Object.entries(stats.methods).map(([method, count]) => (
                <div
                  key={method}
                  className="px-3 py-2 bg-muted rounded-md text-center"
                >
                  <div className="text-xs text-muted-foreground">{method}</div>
                  <div className="text-lg font-semibold">{count}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* APIs List */}
        {stats && stats.apis && stats.apis.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-medium mb-3">Indexed APIs</h4>
            <div className="flex flex-wrap gap-2">
              {stats.apis.map((api, index) => (
                <div
                  key={index}
                  className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-medium"
                >
                  {api}
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
  value: number;
  color: "blue" | "green" | "purple" | "orange";
}

function StatItem({ icon: Icon, label, value, color }: StatItemProps) {
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
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
