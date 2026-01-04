/**
 * Search bar with advanced options
 */

"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { useSearchStore } from "@/lib/stores/searchStore";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isSearching?: boolean;
}

// Generate valid min_score values with custom stepping
// 0.00 to 0.15 in steps of 0.01, then 0.20 to 1.00 in steps of 0.05
const generateMinScoreValues = (): number[] => {
  const values: number[] = [];
  // 0.00 to 0.15 in steps of 0.01
  for (let i = 0; i <= 15; i++) {
    values.push(i / 100);
  }
  // 0.20 to 1.00 in steps of 0.05
  for (let i = 20; i <= 100; i += 5) {
    values.push(i / 100);
  }
  return values;
};

const MIN_SCORE_VALUES = generateMinScoreValues();

export function SearchBar({ onSearch, isSearching }: SearchBarProps) {
  const {
    query,
    setQuery,
    mode,
    setMode,
    useQueryExpansion,
    setUseQueryExpansion,
    resultsLimit,
    setResultsLimit,
    minScore,
    setMinScore,
  } = useSearchStore();

  const [localQuery, setLocalQuery] = useState(query);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setQuery(localQuery);
    onSearch(localQuery);
  };

  // Find the closest index for the current minScore value
  const getMinScoreIndex = () => {
    const index = MIN_SCORE_VALUES.findIndex(v => v === minScore);
    return index >= 0 ? index : 0;
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Search Input */}
          <div className="flex space-x-2">
            <div className="flex-1">
              <Input
                type="text"
                placeholder="Search APIs... (e.g., 'get all users', 'create post endpoint')"
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                className="h-12 text-base"
              />
            </div>
            <Button
              type="submit"
              size="lg"
              disabled={!localQuery.trim() || isSearching}
              className="px-8"
            >
              {isSearching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>

          {/* Advanced Options */}
          <div className="border-t pt-4">
            <Label className="text-sm font-medium mb-3 block">
              Search Options
            </Label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Search Mode */}
              <div className="flex flex-col space-y-2">
                <Label htmlFor="mode" className="text-sm font-medium">
                  Search Mode
                </Label>
                <select
                  id="mode"
                  value={mode}
                  onChange={(e) => setMode(e.target.value as any)}
                  className={cn(
                    "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
                    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  )}
                >
                  <option value="vector">Vector (Fast)</option>
                  <option value="hybrid">Hybrid (BM25 + Vector)</option>
                  <option value="reranked">Reranked (Best Quality)</option>
                </select>
              </div>

              {/* Query Expansion */}
              <OptionToggle
                label="Query Expansion"
                description="Expand query with synonyms"
                checked={useQueryExpansion}
                onChange={setUseQueryExpansion}
              />

              {/* Results Limit */}
              <div className="flex flex-col space-y-2">
                <Label htmlFor="limit" className="text-sm font-medium">
                  Results Limit
                </Label>
                <select
                  id="limit"
                  value={resultsLimit}
                  onChange={(e) => setResultsLimit(Number(e.target.value))}
                  className={cn(
                    "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
                    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  )}
                >
                  <option value={5}>5 results</option>
                  <option value={10}>10 results</option>
                  <option value={20}>20 results</option>
                  <option value={50}>50 results</option>
                </select>
              </div>

              {/* Min Score Slider */}
              <div className="flex flex-col space-y-2">
                <Label htmlFor="minScore" className="text-sm font-medium">
                  Min Score: {minScore.toFixed(2)}
                  {minScore === 0 && <span className="text-xs text-muted-foreground ml-1">(No filter)</span>}
                </Label>
                <input
                  type="range"
                  id="minScore"
                  min="0"
                  max={MIN_SCORE_VALUES.length - 1}
                  value={getMinScoreIndex()}
                  onChange={(e) => {
                    const index = parseInt(e.target.value);
                    setMinScore(MIN_SCORE_VALUES[index]);
                  }}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0.00</span>
                  <span>0.15</span>
                  <span>1.00</span>
                </div>
              </div>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

interface OptionToggleProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function OptionToggle({ label, description, checked, onChange }: OptionToggleProps) {
  return (
    <div className="flex items-start space-x-2">
      <input
        type="checkbox"
        id={label}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className={cn(
          "mt-1 h-4 w-4 rounded border-gray-300 text-primary",
          "focus:ring-2 focus:ring-primary focus:ring-offset-2"
        )}
      />
      <div className="flex-1">
        <Label htmlFor={label} className="text-sm font-medium cursor-pointer">
          {label}
        </Label>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
