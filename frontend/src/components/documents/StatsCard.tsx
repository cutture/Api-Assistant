/**
 * Collection statistics card component
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCollectionStats } from "@/hooks/useDocuments";
import { Skeleton } from "@/components/ui/skeleton";
import { Database, FileText, Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Feature descriptions for user guidance
const FEATURE_INFO = {
  hybrid_search: {
    name: "Hybrid Search",
    description: "Combines BM25 keyword search with vector similarity search using Reciprocal Rank Fusion. Best for technical queries with specific terms.",
    shortDesc: "BM25 + Vector search"
  },
  reranking: {
    name: "Reranking",
    description: "Uses cross-encoder models to deeply analyze and re-rank search results for maximum relevance. Slower but most accurate.",
    shortDesc: "Cross-encoder re-ranking"
  },
  query_expansion: {
    name: "Query Expansion",
    description: "Automatically expands queries with synonyms, related terms, and technical abbreviations to improve search recall.",
    shortDesc: "Synonym & term expansion"
  },
  diversification: {
    name: "Diversification",
    description: "Uses MMR algorithm to reduce redundancy in search results by ensuring diversity while maintaining relevance.",
    shortDesc: "MMR diversity algorithm"
  },
  faceted_search: {
    name: "Faceted Search",
    description: "Enables filtering and grouping of search results by metadata fields (source, method, API name) for better organization.",
    shortDesc: "Metadata-based filtering"
  },
  filtering: {
    name: "Filtering",
    description: "Advanced boolean filtering with 13 operators (eq, in, contains, regex, etc.) for precise document queries.",
    shortDesc: "Advanced boolean filters"
  },
};

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
            <TooltipProvider>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(stats.features).map(([feature, enabled]) => {
                  const featureInfo = FEATURE_INFO[feature as keyof typeof FEATURE_INFO];
                  return (
                    <div
                      key={feature}
                      className={`relative px-3 py-3 rounded-md border ${
                        enabled
                          ? "bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-900"
                          : "bg-muted border-border"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-medium capitalize mb-0.5">
                            {featureInfo?.name || feature.replace(/_/g, " ")}
                          </div>
                          {featureInfo?.shortDesc && (
                            <div className="text-[10px] text-muted-foreground line-clamp-1">
                              {featureInfo.shortDesc}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          {featureInfo && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button className="p-0.5 hover:bg-background/50 rounded transition-colors">
                                  <Info className="h-3 w-3 text-muted-foreground" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent className="max-w-xs">
                                <p className="text-xs">{featureInfo.description}</p>
                              </TooltipContent>
                            </Tooltip>
                          )}
                          <div className="text-sm font-semibold">
                            {enabled ? "✓" : "✗"}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </TooltipProvider>
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
