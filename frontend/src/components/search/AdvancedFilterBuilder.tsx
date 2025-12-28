/**
 * Advanced filter builder with AND/OR/NOT logic
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Filter as FilterIcon, Plus, Trash2, X } from "lucide-react";
import { Filter, SearchFilters } from "@/types";
import { cn } from "@/lib/utils";

interface AdvancedFilterBuilderProps {
  onFiltersChange: (filters: SearchFilters | null) => void;
}

export function AdvancedFilterBuilder({ onFiltersChange }: AdvancedFilterBuilderProps) {
  const [operator, setOperator] = useState<"and" | "or" | "not">("and");
  const [filters, setFilters] = useState<Filter[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const addFilter = () => {
    const newFilter: Filter = {
      field: "method",
      operator: "eq",
      value: "",
    };
    const updated = [...filters, newFilter];
    setFilters(updated);
    emitFilters(updated);
  };

  const updateFilter = (index: number, updates: Partial<Filter>) => {
    const updated = filters.map((f, i) => (i === index ? { ...f, ...updates } : f));
    setFilters(updated);
    emitFilters(updated);
  };

  const removeFilter = (index: number) => {
    const updated = filters.filter((_, i) => i !== index);
    setFilters(updated);
    emitFilters(updated);
  };

  const clearAllFilters = () => {
    setFilters([]);
    onFiltersChange(null);
  };

  const emitFilters = (currentFilters: Filter[]) => {
    if (currentFilters.length === 0) {
      onFiltersChange(null);
      return;
    }

    const validFilters = currentFilters.filter((f) => f.value !== "");
    if (validFilters.length === 0) {
      onFiltersChange(null);
      return;
    }

    onFiltersChange({
      operator,
      filters: validFilters,
    });
  };

  const handleOperatorChange = (newOperator: "and" | "or" | "not") => {
    setOperator(newOperator);
    if (filters.length > 0) {
      onFiltersChange({
        operator: newOperator,
        filters: filters.filter((f) => f.value !== ""),
      });
    }
  };

  if (!isOpen) {
    return (
      <Button
        variant="outline"
        onClick={() => setIsOpen(true)}
        className="w-full"
      >
        <FilterIcon className="mr-2 h-4 w-4" />
        Advanced Filters
      </Button>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2 text-base">
              <FilterIcon className="h-4 w-4" />
              <span>Advanced Filter Builder</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Build complex filter expressions
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setIsOpen(false);
              clearAllFilters();
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Operator Selection */}
        <div className="space-y-2">
          <Label className="text-sm">Logical Operator</Label>
          <div className="flex space-x-2">
            <Button
              variant={operator === "and" ? "default" : "outline"}
              size="sm"
              onClick={() => handleOperatorChange("and")}
              className="flex-1"
            >
              AND
            </Button>
            <Button
              variant={operator === "or" ? "default" : "outline"}
              size="sm"
              onClick={() => handleOperatorChange("or")}
              className="flex-1"
            >
              OR
            </Button>
            <Button
              variant={operator === "not" ? "default" : "outline"}
              size="sm"
              onClick={() => handleOperatorChange("not")}
              className="flex-1"
            >
              NOT
            </Button>
          </div>
        </div>

        {/* Filters List */}
        <div className="space-y-3">
          {filters.map((filter, index) => (
            <FilterRow
              key={index}
              filter={filter}
              onUpdate={(updates) => updateFilter(index, updates)}
              onRemove={() => removeFilter(index)}
            />
          ))}
        </div>

        {/* Actions */}
        <div className="flex justify-between pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={addFilter}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Filter
          </Button>
          {filters.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear All
            </Button>
          )}
        </div>

        {/* Active Filters Summary */}
        {filters.filter((f) => f.value !== "").length > 0 && (
          <div className="pt-4 border-t">
            <Label className="text-sm mb-2 block">Active Expression</Label>
            <div className="p-3 bg-muted rounded-md text-xs font-mono">
              {operator.toUpperCase()}{" "}
              (
              {filters
                .filter((f) => f.value !== "")
                .map((f, i) => (
                  <span key={i}>
                    {i > 0 && `, `}
                    {f.field} {f.operator} "{f.value}"
                  </span>
                ))}
              )
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface FilterRowProps {
  filter: Filter;
  onUpdate: (updates: Partial<Filter>) => void;
  onRemove: () => void;
}

function FilterRow({ filter, onUpdate, onRemove }: FilterRowProps) {
  const fields = [
    { value: "method", label: "HTTP Method" },
    { value: "source", label: "Source Type" },
    { value: "api_name", label: "API Name" },
    { value: "endpoint", label: "Endpoint" },
    { value: "path", label: "Path" },
    { value: "tags", label: "Tags" },
  ];

  const operators = [
    { value: "eq", label: "equals" },
    { value: "ne", label: "not equals" },
    { value: "contains", label: "contains" },
    { value: "in", label: "in" },
    { value: "nin", label: "not in" },
  ];

  return (
    <div className="flex items-end space-x-2 p-3 border rounded-lg bg-muted/30">
      <div className="flex-1 space-y-1">
        <Label className="text-xs">Field</Label>
        <select
          value={filter.field}
          onChange={(e) => onUpdate({ field: e.target.value })}
          className={cn(
            "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          )}
        >
          {fields.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 space-y-1">
        <Label className="text-xs">Operator</Label>
        <select
          value={filter.operator}
          onChange={(e) => onUpdate({ operator: e.target.value as any })}
          className={cn(
            "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          )}
        >
          {operators.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 space-y-1">
        <Label className="text-xs">Value</Label>
        <Input
          value={filter.value}
          onChange={(e) => onUpdate({ value: e.target.value })}
          placeholder="Enter value..."
          className="h-9"
        />
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="h-9 w-9 p-0"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
