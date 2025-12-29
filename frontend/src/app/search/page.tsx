/**
 * Search page - Advanced search interface
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { FilterPanel } from "@/components/search/FilterPanel";
import { AdvancedFilterBuilder } from "@/components/search/AdvancedFilterBuilder";
import { FacetedSearch } from "@/components/search/FacetedSearch";
import { useSearch, useFacetedSearch } from "@/hooks/useSearch";
import { useSearchStore } from "@/lib/stores/searchStore";
import { Filter, SearchRequest, SearchFilters } from "@/types";
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function SearchPage() {
  const { mutate: search } = useSearch();
  const { mutate: facetedSearch } = useFacetedSearch();
  const { mode, useQueryExpansion, resultsLimit } = useSearchStore();
  const [simpleFilters, setSimpleFilters] = useState<Filter[]>([]);
  const [advancedFilters, setAdvancedFilters] = useState<SearchFilters | null>(null);
  const [facets, setFacets] = useState<any[]>([]);
  const [useFacets, setUseFacets] = useState(false);
  const [filterMode, setFilterMode] = useState<"simple" | "advanced">("simple");

  const handleSearch = (query: string) => {
    if (!query.trim()) return;

    const request: SearchRequest = {
      query,
      n_results: resultsLimit,
      mode: mode,
      use_query_expansion: useQueryExpansion,
    };

    // Add filters based on mode
    if (filterMode === "simple" && simpleFilters.length > 0) {
      request.filter = {
        operator: "and",
        filters: simpleFilters,
      };
    } else if (filterMode === "advanced" && advancedFilters) {
      request.filter = advancedFilters;
    }

    // Use faceted search if enabled
    if (useFacets) {
      facetedSearch(
        { ...request, facet_fields: ["source", "method", "api_name"] },
        {
          onSuccess: (data) => {
            if (data?.facets) {
              setFacets(data.facets);
            }
          },
        }
      );
    } else {
      search(request);
    }
  };

  const handleFacetSelect = (field: string, value: any) => {
    const newFilter: Filter = {
      field,
      operator: "eq",
      value,
    };
    if (filterMode === "simple") {
      setSimpleFilters([...simpleFilters, newFilter]);
    }
  };

  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">API Search</h1>
          <p className="text-muted-foreground mt-2">
            Search through your indexed API documentation with advanced filters
          </p>
        </div>

        <SearchBar onSearch={handleSearch} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            <Tabs value={filterMode} onValueChange={(v: string) => setFilterMode(v as "simple" | "advanced")}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="simple">Simple</TabsTrigger>
                <TabsTrigger value="advanced">Advanced</TabsTrigger>
              </TabsList>
              <TabsContent value="simple" className="space-y-4 mt-4">
                <FilterPanel onFiltersChange={setSimpleFilters} />
              </TabsContent>
              <TabsContent value="advanced" className="mt-4">
                <AdvancedFilterBuilder onFiltersChange={setAdvancedFilters} />
              </TabsContent>
            </Tabs>

            {useFacets && facets.length > 0 && (
              <FacetedSearch facets={facets} onFacetSelect={handleFacetSelect} />
            )}
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            <SearchResults />
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
