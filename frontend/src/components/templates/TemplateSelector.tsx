'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  Code2,
  FileCode,
  Database,
  Shield,
  TestTube,
  Wrench,
  Layout,
  Link2,
  ChevronRight,
  Search,
  Star,
  Check,
} from 'lucide-react';

export interface TemplateParameter {
  name: string;
  description: string;
  type: string;
  required: boolean;
  default?: any;
  enum_values?: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  language: string;
  tags: string[];
  usage_count: number;
  is_builtin: boolean;
  parameters?: TemplateParameter[];
}

interface TemplateSelectorProps {
  templates: Template[];
  selectedTemplate?: Template;
  onSelect: (template: Template) => void;
  onRender?: (templateId: string, params: Record<string, any>) => void;
  isLoading?: boolean;
  className?: string;
}

const categoryIcons: Record<string, React.ElementType> = {
  rest_api: Code2,
  crud: FileCode,
  database: Database,
  authentication: Shield,
  testing: TestTube,
  utility: Wrench,
  frontend: Layout,
  integration: Link2,
};

const languageColors: Record<string, string> = {
  python: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  javascript: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  typescript: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  java: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  go: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  csharp: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  any: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

function TemplateCard({
  template,
  isSelected,
  onClick,
}: {
  template: Template;
  isSelected: boolean;
  onClick: () => void;
}) {
  const CategoryIcon = categoryIcons[template.category] || Code2;
  const langColor = languageColors[template.language] || languageColors.any;

  return (
    <div
      onClick={onClick}
      className={cn(
        'relative rounded-lg border p-4 cursor-pointer transition-all',
        'hover:border-primary hover:shadow-sm',
        isSelected && 'border-primary bg-primary/5 ring-1 ring-primary'
      )}
    >
      {isSelected && (
        <div className="absolute top-2 right-2">
          <Check className="h-5 w-5 text-primary" />
        </div>
      )}

      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-muted">
          <CategoryIcon className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium truncate">{template.name}</h3>
            {template.is_builtin && (
              <Star className="h-3 w-3 text-yellow-500 flex-shrink-0" />
            )}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {template.description}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3 flex-wrap">
        <span className={cn('text-xs px-2 py-0.5 rounded font-medium', langColor)}>
          {template.language}
        </span>
        {template.tags.slice(0, 2).map((tag) => (
          <span
            key={tag}
            className="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground"
          >
            {tag}
          </span>
        ))}
        {template.usage_count > 0 && (
          <span className="text-xs text-muted-foreground ml-auto">
            {template.usage_count} uses
          </span>
        )}
      </div>
    </div>
  );
}

function ParameterInput({
  param,
  value,
  onChange,
}: {
  param: TemplateParameter;
  value: any;
  onChange: (value: any) => void;
}) {
  if (param.enum_values) {
    return (
      <select
        value={value ?? param.default ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border bg-background px-3 py-2 text-sm"
      >
        <option value="">Select {param.name}</option>
        {param.enum_values.map((val) => (
          <option key={val} value={val}>
            {val}
          </option>
        ))}
      </select>
    );
  }

  if (param.type === 'boolean') {
    return (
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={value ?? param.default ?? false}
          onChange={(e) => onChange(e.target.checked)}
          className="rounded border-gray-300"
        />
        <span className="text-sm">{param.description}</span>
      </label>
    );
  }

  if (param.type === 'number') {
    return (
      <input
        type="number"
        value={value ?? param.default ?? ''}
        onChange={(e) => onChange(parseInt(e.target.value) || 0)}
        placeholder={param.description}
        className="w-full rounded-md border bg-background px-3 py-2 text-sm"
      />
    );
  }

  return (
    <input
      type="text"
      value={value ?? param.default ?? ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={param.description}
      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
    />
  );
}

export function TemplateSelector({
  templates,
  selectedTemplate,
  onSelect,
  onRender,
  isLoading,
  className,
}: TemplateSelectorProps) {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [categoryFilter, setCategoryFilter] = React.useState<string | null>(null);
  const [languageFilter, setLanguageFilter] = React.useState<string | null>(null);
  const [params, setParams] = React.useState<Record<string, any>>({});

  // Get unique categories and languages
  const categories = React.useMemo(() => {
    const cats = new Set(templates.map((t) => t.category));
    return Array.from(cats).sort();
  }, [templates]);

  const languages = React.useMemo(() => {
    const langs = new Set(templates.map((t) => t.language));
    return Array.from(langs).sort();
  }, [templates]);

  // Filter templates
  const filteredTemplates = React.useMemo(() => {
    return templates.filter((t) => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesName = t.name.toLowerCase().includes(query);
        const matchesDesc = t.description.toLowerCase().includes(query);
        const matchesTags = t.tags.some((tag) => tag.toLowerCase().includes(query));
        if (!matchesName && !matchesDesc && !matchesTags) return false;
      }
      if (categoryFilter && t.category !== categoryFilter) return false;
      if (languageFilter && t.language !== languageFilter) return false;
      return true;
    });
  }, [templates, searchQuery, categoryFilter, languageFilter]);

  const handleParamChange = (name: string, value: any) => {
    setParams((prev) => ({ ...prev, [name]: value }));
  };

  const handleRender = () => {
    if (selectedTemplate && onRender) {
      onRender(selectedTemplate.id, params);
    }
  };

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Search and filters */}
      <div className="space-y-3 mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border bg-background text-sm"
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          <select
            value={categoryFilter ?? ''}
            onChange={(e) => setCategoryFilter(e.target.value || null)}
            className="text-sm rounded-md border bg-background px-2 py-1"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.replace(/_/g, ' ')}
              </option>
            ))}
          </select>

          <select
            value={languageFilter ?? ''}
            onChange={(e) => setLanguageFilter(e.target.value || null)}
            className="text-sm rounded-md border bg-background px-2 py-1"
          >
            <option value="">All Languages</option>
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {lang}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Template list */}
      <div className="flex-1 overflow-y-auto space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            Loading templates...
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No templates found
          </div>
        ) : (
          filteredTemplates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              isSelected={selectedTemplate?.id === template.id}
              onClick={() => {
                onSelect(template);
                setParams({});
              }}
            />
          ))
        )}
      </div>

      {/* Selected template parameters */}
      {selectedTemplate?.parameters && selectedTemplate.parameters.length > 0 && (
        <div className="mt-4 pt-4 border-t space-y-3">
          <h4 className="text-sm font-medium">Template Parameters</h4>
          {selectedTemplate.parameters.map((param) => (
            <div key={param.name} className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                {param.name}
                {param.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              <ParameterInput
                param={param}
                value={params[param.name]}
                onChange={(value) => handleParamChange(param.name, value)}
              />
            </div>
          ))}

          {onRender && (
            <button
              onClick={handleRender}
              className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              <Code2 className="h-4 w-4" />
              Use Template
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default TemplateSelector;
