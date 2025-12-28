/**
 * Search results display component
 */

"use client";

import { SearchResult } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Globe, Code, AlertCircle } from "lucide-react";
import { useSearchStore } from "@/lib/stores/searchStore";

export function SearchResults() {
  const { results, isSearching, searchError, searchTime, query } = useSearchStore();

  if (isSearching) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center text-muted-foreground">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
            <p>Searching...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (searchError) {
    return (
      <Card className="border-destructive">
        <CardContent className="py-12">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-destructive mb-4" />
            <p className="text-sm font-medium text-destructive">Search Error</p>
            <p className="text-xs text-muted-foreground mt-2">{searchError}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!query) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center text-muted-foreground">
            <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p>Enter a search query to begin</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (results.length === 0) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center text-muted-foreground">
            <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
            <p className="font-medium">No results found</p>
            <p className="text-xs mt-2">
              Try adjusting your search query or filters
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Results Header */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <p>
          Found <span className="font-medium text-foreground">{results.length}</span> results
        </p>
        <p>Search time: {searchTime.toFixed(0)}ms</p>
      </div>

      {/* Results List */}
      <div className="space-y-3">
        {results.map((result, index) => (
          <SearchResultCard key={index} result={result} rank={index + 1} />
        ))}
      </div>
    </div>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
  rank: number;
}

function SearchResultCard({ result, rank }: SearchResultCardProps) {
  const { document, score } = result;
  const metadata = document.metadata;

  const getSourceIcon = (source: string) => {
    switch (source) {
      case "openapi":
        return Globe;
      case "graphql":
        return Code;
      case "postman":
        return FileText;
      default:
        return FileText;
    }
  };

  const SourceIcon = getSourceIcon(metadata.source);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-medium">
                {rank}
              </span>
              <SourceIcon className="h-4 w-4 text-muted-foreground" />
              <Badge variant="outline" className="text-xs">
                {metadata.source}
              </Badge>
              {metadata.method && (
                <Badge
                  variant={
                    metadata.method === "GET"
                      ? "default"
                      : metadata.method === "POST"
                      ? "secondary"
                      : "outline"
                  }
                  className="text-xs"
                >
                  {metadata.method}
                </Badge>
              )}
            </div>
            <CardTitle className="text-lg">
              {metadata.endpoint || metadata.path || metadata.summary || "Untitled"}
            </CardTitle>
            {metadata.api_name && (
              <CardDescription className="mt-1">
                {metadata.api_name}
              </CardDescription>
            )}
          </div>
          <div className="text-right">
            <div className="text-sm font-medium">
              Score: {(score * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {metadata.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {metadata.description}
            </p>
          )}

          {metadata.tags && metadata.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {metadata.tags.slice(0, 5).map((tag, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {metadata.tags.length > 5 && (
                <Badge variant="secondary" className="text-xs">
                  +{metadata.tags.length - 5} more
                </Badge>
              )}
            </div>
          )}

          {/* Content Preview */}
          {document.content && (
            <details className="mt-3">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Show details
              </summary>
              <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-x-auto">
                {document.content.slice(0, 500)}
                {document.content.length > 500 && "..."}
              </pre>
            </details>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
