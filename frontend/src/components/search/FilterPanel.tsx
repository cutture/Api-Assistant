/**
 * Filter panel for search
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { X, Filter } from "lucide-react";
import { Filter as FilterType } from "@/types";

interface FilterPanelProps {
  onFiltersChange: (filters: FilterType[]) => void;
}

export function FilterPanel({ onFiltersChange }: FilterPanelProps) {
  const [filters, setFilters] = useState<FilterType[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>("");
  const [selectedSource, setSelectedSource] = useState<string>("");

  const methods = ["GET", "POST", "PUT", "DELETE", "PATCH"];
  const sources = ["openapi", "graphql", "postman"];

  const addMethodFilter = (method: string) => {
    if (!method) return;

    const newFilter: FilterType = {
      field: "method",
      operator: "eq",
      value: method,
    };

    const updated = [...filters, newFilter];
    setFilters(updated);
    onFiltersChange(updated);
    setSelectedMethod("");
  };

  const addSourceFilter = (source: string) => {
    if (!source) return;

    const newFilter: FilterType = {
      field: "source",
      operator: "eq",
      value: source,
    };

    const updated = [...filters, newFilter];
    setFilters(updated);
    onFiltersChange(updated);
    setSelectedSource("");
  };

  const removeFilter = (index: number) => {
    const updated = filters.filter((_, i) => i !== index);
    setFilters(updated);
    onFiltersChange(updated);
  };

  const clearAllFilters = () => {
    setFilters([]);
    onFiltersChange([]);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2 text-base">
          <Filter className="h-4 w-4" />
          <span>Filters</span>
        </CardTitle>
        <CardDescription className="text-xs">
          Refine your search results
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Method Filter */}
        <div className="space-y-2">
          <Label className="text-sm">HTTP Method</Label>
          <div className="flex flex-wrap gap-2">
            {methods.map((method) => (
              <Button
                key={method}
                variant="outline"
                size="sm"
                onClick={() => addMethodFilter(method)}
                disabled={filters.some(
                  (f) => f.field === "method" && f.value === method
                )}
                className="text-xs"
              >
                {method}
              </Button>
            ))}
          </div>
        </div>

        {/* Source Filter */}
        <div className="space-y-2">
          <Label className="text-sm">Source Type</Label>
          <div className="flex flex-wrap gap-2">
            {sources.map((source) => (
              <Button
                key={source}
                variant="outline"
                size="sm"
                onClick={() => addSourceFilter(source)}
                disabled={filters.some(
                  (f) => f.field === "source" && f.value === source
                )}
                className="text-xs capitalize"
              >
                {source}
              </Button>
            ))}
          </div>
        </div>

        {/* Active Filters */}
        {filters.length > 0 && (
          <div className="space-y-2 pt-4 border-t">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Active Filters</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFilters}
                className="text-xs h-7"
              >
                Clear All
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {filters.map((filter, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="text-xs flex items-center space-x-1 pr-1"
                >
                  <span>
                    {filter.field}: {filter.value}
                  </span>
                  <button
                    onClick={() => removeFilter(index)}
                    className="ml-1 hover:bg-destructive hover:text-destructive-foreground rounded-full p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
