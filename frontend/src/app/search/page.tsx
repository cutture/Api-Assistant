/**
 * Search page - Advanced search interface
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { FilterPanel } from "@/components/search/FilterPanel";
import { FacetedSearch } from "@/components/search/FacetedSearch";
import { useSearch, useFacetedSearch } from "@/hooks/useSearch";
import { useSearchStore } from "@/lib/stores/searchStore";
import { Filter, SearchRequest } from "@/types";
import { useState } from "react";

export default function SearchPage() {
  const { mutate: search } = useSearch();
  const { mutate: facetedSearch } = useFacetedSearch();
  const { useHybrid, useReranking, useQueryExpansion, resultsLimit } = useSearchStore();
  const [filters, setFilters] = useState<Filter[]>([]);
  const [facets, setFacets] = useState<any[]>([]);
  const [useFacets, setUseFacets] = useState(false);

  const handleSearch = (query: string) => {
    if (!query.trim()) return;

    const request: SearchRequest = {
      query,
      n_results: resultsLimit,
      use_hybrid: useHybrid,
      use_reranking: useReranking,
      use_query_expansion: useQueryExpansion,
    };

    // Add filters if any
    if (filters.length > 0) {
      request.filters = {
        operator: "and",
        filters: filters,
      };
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
    setFilters([...filters, newFilter]);
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
            <FilterPanel onFiltersChange={setFilters} />
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
