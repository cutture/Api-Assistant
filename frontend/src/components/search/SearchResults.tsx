/**
 * Search results display component
 */

"use client";

import { SearchResult } from "@/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Globe, Code, AlertCircle, Copy, Check, ChevronLeft, ChevronRight } from "lucide-react";
import { useSearchStore } from "@/lib/stores/searchStore";
import { useState, useMemo } from "react";
import { useToast } from "@/hooks/use-toast";

export function SearchResults() {
  const { results, isSearching, searchError, searchTime, query, currentPage, resultsLimit, setCurrentPage } = useSearchStore();

  // Calculate pagination
  const totalPages = Math.ceil(results.length / resultsLimit);
  const paginatedResults = useMemo(() => {
    const startIndex = (currentPage - 1) * resultsLimit;
    const endIndex = startIndex + resultsLimit;
    return results.slice(startIndex, endIndex);
  }, [results, currentPage, resultsLimit]);

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
          {totalPages > 1 && (
            <span className="ml-2">
              (Page {currentPage} of {totalPages})
            </span>
          )}
        </p>
        <p>Search time: {searchTime.toFixed(0)}ms</p>
      </div>

      {/* Top Pagination Controls */}
      {totalPages > 1 && (
        <Card>
          <CardContent className="py-3">
            <PaginationControls
              currentPage={currentPage}
              totalPages={totalPages}
              results={results}
              resultsLimit={resultsLimit}
              onPageChange={setCurrentPage}
            />
          </CardContent>
        </Card>
      )}

      {/* Results List */}
      <div className="space-y-3">
        {paginatedResults.map((result, index) => (
          <SearchResultCard
            key={index}
            result={result}
            rank={(currentPage - 1) * resultsLimit + index + 1}
          />
        ))}
      </div>

      {/* Bottom Pagination Controls */}
      {totalPages > 1 && (
        <Card>
          <CardContent className="py-4">
            <PaginationControls
              currentPage={currentPage}
              totalPages={totalPages}
              results={results}
              resultsLimit={resultsLimit}
              onPageChange={setCurrentPage}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Separate pagination component for reusability
interface PaginationControlsProps {
  currentPage: number;
  totalPages: number;
  results: SearchResult[];
  resultsLimit: number;
  onPageChange: (page: number) => void;
}

function PaginationControls({
  currentPage,
  totalPages,
  results,
  resultsLimit,
  onPageChange,
}: PaginationControlsProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-muted-foreground">
        Showing {(currentPage - 1) * resultsLimit + 1} to{" "}
        {Math.min(currentPage * resultsLimit, results.length)} of {results.length} results
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        <div className="flex items-center gap-1">
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            let pageNumber;
            if (totalPages <= 5) {
              pageNumber = i + 1;
            } else if (currentPage <= 3) {
              pageNumber = i + 1;
            } else if (currentPage >= totalPages - 2) {
              pageNumber = totalPages - 4 + i;
            } else {
              pageNumber = currentPage - 2 + i;
            }

            return (
              <Button
                key={i}
                variant={currentPage === pageNumber ? "default" : "outline"}
                size="sm"
                onClick={() => onPageChange(pageNumber)}
                className="w-9"
              >
                {pageNumber}
              </Button>
            );
          })}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
        >
          Next
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
  rank: number;
}

function SearchResultCard({ result, rank }: SearchResultCardProps) {
  const { id, content, metadata, score } = result;
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

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

  const SourceIcon = getSourceIcon(metadata?.source || "");

  // Handle tags - backend stores as comma-separated string
  const tags: string[] = metadata?.tags
    ? (Array.isArray(metadata.tags)
        ? metadata.tags
        : (metadata.tags as string).split(',').filter((t: string) => t.trim()))
    : [];

  const copyToClipboard = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    toast({
      title: "Document ID copied",
      description: "Use this ID to generate sequence diagrams",
    });
    setTimeout(() => setCopied(false), 2000);
  };

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
              {metadata?.source && (
                <Badge variant="outline" className="text-xs">
                  {metadata.source}
                </Badge>
              )}
              {metadata?.method && (
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
              {metadata?.endpoint || metadata?.path || metadata?.summary || metadata?.title || metadata?.source_file || "Untitled"}
            </CardTitle>
            {metadata?.api_name && (
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
          {metadata?.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {metadata.description}
            </p>
          )}

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {tags.slice(0, 5).map((tag: string, i: number) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {tags.length > 5 && (
                <Badge variant="secondary" className="text-xs">
                  +{tags.length - 5} more
                </Badge>
              )}
            </div>
          )}

          {/* Content Preview */}
          {content && (
            <details className="mt-3">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Show details
              </summary>
              <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-x-auto">
                {content.slice(0, 500)}
                {content.length > 500 && "..."}
              </pre>
            </details>
          )}

          {/* Document ID */}
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0">
                <label className="text-xs text-muted-foreground font-medium">
                  Document ID
                </label>
                <p className="text-xs font-mono text-muted-foreground mt-1 truncate">
                  {id}
                </p>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={copyToClipboard}
                className="shrink-0"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    Copy ID
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
