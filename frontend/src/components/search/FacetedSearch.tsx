/**
 * Faceted search component with aggregations
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layers } from "lucide-react";
import { Facet } from "@/types";

interface FacetedSearchProps {
  facets: Facet[];
  onFacetSelect: (field: string, value: any) => void;
}

export function FacetedSearch({ facets, onFacetSelect }: FacetedSearchProps) {
  if (!facets || facets.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2 text-base">
          <Layers className="h-4 w-4" />
          <span>Faceted Browse</span>
        </CardTitle>
        <CardDescription className="text-xs">
          Explore results by category
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {facets.map((facet) => (
          <FacetGroup
            key={facet.field}
            facet={facet}
            onSelect={(value) => onFacetSelect(facet.field, value)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

interface FacetGroupProps {
  facet: Facet;
  onSelect: (value: any) => void;
}

function FacetGroup({ facet, onSelect }: FacetGroupProps) {
  const [expanded, setExpanded] = useState(true);

  const displayValues = expanded ? facet.values : facet.values.slice(0, 5);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium capitalize">{facet.field}</h4>
        <Badge variant="outline" className="text-xs">
          {facet.values.length}
        </Badge>
      </div>
      <div className="space-y-1">
        {displayValues.map((valueData, index) => (
          <button
            key={index}
            onClick={() => onSelect(valueData.value)}
            className="w-full flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-muted text-left text-sm transition-colors"
          >
            <span className="text-muted-foreground">{valueData.value}</span>
            <Badge variant="secondary" className="text-xs">
              {valueData.count}
            </Badge>
          </button>
        ))}
      </div>
      {facet.values.length > 5 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="w-full text-xs"
        >
          {expanded ? "Show Less" : `Show ${facet.values.length - 5} More`}
        </Button>
      )}
    </div>
  );
}
