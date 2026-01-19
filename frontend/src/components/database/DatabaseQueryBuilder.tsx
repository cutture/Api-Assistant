'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  Database,
  Play,
  Copy,
  AlertTriangle,
  CheckCircle,
  Info,
  XCircle,
  ChevronDown,
  ChevronUp,
  FileCode,
  Lightbulb,
} from 'lucide-react';

export type DatabaseType = 'postgresql' | 'mysql' | 'sqlite' | 'mongodb';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  risk_level: RiskLevel;
  query_type: string | null;
  affected_tables: string[];
  has_where_clause: boolean;
  is_parameterized: boolean;
}

export interface QueryExplanation {
  summary: string;
  query_type: string;
  database_type: string;
  tables_involved: string[];
  columns_involved: string[];
  conditions: string[];
  operations: string[];
  performance_hints: string[];
  security_notes: string[];
}

export interface GeneratedQuery {
  query: string;
  database_type: string;
  query_type: string;
  parameters: Record<string, any>;
  validation: ValidationResult | null;
  explanation: QueryExplanation | null;
}

interface DatabaseQueryBuilderProps {
  onExecute?: (query: string, dbType: DatabaseType) => void;
  onCopy?: (query: string) => void;
  initialQuery?: string;
  initialDbType?: DatabaseType;
  className?: string;
}

const databaseOptions: { value: DatabaseType; label: string; icon: string }[] = [
  { value: 'postgresql', label: 'PostgreSQL', icon: '🐘' },
  { value: 'mysql', label: 'MySQL', icon: '🐬' },
  { value: 'sqlite', label: 'SQLite', icon: '📦' },
  { value: 'mongodb', label: 'MongoDB', icon: '🍃' },
];

const riskColors: Record<RiskLevel, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

const RiskIcon: React.FC<{ level: RiskLevel }> = ({ level }) => {
  switch (level) {
    case 'low':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'medium':
      return <Info className="h-4 w-4 text-yellow-500" />;
    case 'high':
      return <AlertTriangle className="h-4 w-4 text-orange-500" />;
    case 'critical':
      return <XCircle className="h-4 w-4 text-red-500" />;
  }
};

function ValidationPanel({ validation }: { validation: ValidationResult }) {
  const colors = riskColors[validation.risk_level];

  return (
    <div className={cn('rounded-lg border p-4', colors.bg, colors.border)}>
      <div className="flex items-center gap-2 mb-3">
        <RiskIcon level={validation.risk_level} />
        <span className={cn('font-medium', colors.text)}>
          {validation.risk_level.charAt(0).toUpperCase() + validation.risk_level.slice(1)} Risk
        </span>
        {validation.query_type && (
          <span className="ml-auto text-xs px-2 py-0.5 rounded bg-white/50">
            {validation.query_type.toUpperCase()}
          </span>
        )}
      </div>

      {validation.errors.length > 0 && (
        <div className="space-y-1 mb-3">
          <p className="text-xs font-medium text-red-600">Errors:</p>
          {validation.errors.map((error, i) => (
            <p key={i} className="text-sm text-red-600 flex items-start gap-1">
              <XCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
              {error}
            </p>
          ))}
        </div>
      )}

      {validation.warnings.length > 0 && (
        <div className="space-y-1 mb-3">
          <p className="text-xs font-medium text-amber-600">Warnings:</p>
          {validation.warnings.map((warning, i) => (
            <p key={i} className="text-sm text-amber-600 flex items-start gap-1">
              <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />
              {warning}
            </p>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-2 text-xs">
        {validation.affected_tables.length > 0 && (
          <span className="px-2 py-0.5 rounded bg-white/50">
            Tables: {validation.affected_tables.join(', ')}
          </span>
        )}
        {validation.has_where_clause && (
          <span className="px-2 py-0.5 rounded bg-green-100 text-green-700">
            Has WHERE
          </span>
        )}
        {validation.is_parameterized && (
          <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700">
            Parameterized
          </span>
        )}
      </div>
    </div>
  );
}

function ExplanationPanel({ explanation }: { explanation: QueryExplanation }) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div className="rounded-lg border bg-blue-50 border-blue-200 p-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 w-full text-left"
      >
        <Lightbulb className="h-4 w-4 text-blue-500" />
        <span className="font-medium text-blue-700 flex-1">{explanation.summary}</span>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-blue-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-blue-500" />
        )}
      </button>

      {expanded && (
        <div className="mt-3 space-y-3 text-sm">
          {explanation.operations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-blue-600 mb-1">Operations:</p>
              <ul className="list-disc list-inside text-blue-700 space-y-0.5">
                {explanation.operations.map((op, i) => (
                  <li key={i}>{op}</li>
                ))}
              </ul>
            </div>
          )}

          {explanation.tables_involved.length > 0 && (
            <div>
              <p className="text-xs font-medium text-blue-600 mb-1">Tables:</p>
              <div className="flex flex-wrap gap-1">
                {explanation.tables_involved.map((table, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-white text-blue-700 text-xs"
                  >
                    {table}
                  </span>
                ))}
              </div>
            </div>
          )}

          {explanation.columns_involved.length > 0 && (
            <div>
              <p className="text-xs font-medium text-blue-600 mb-1">Columns:</p>
              <div className="flex flex-wrap gap-1">
                {explanation.columns_involved.map((col, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-white text-blue-700 text-xs"
                  >
                    {col}
                  </span>
                ))}
              </div>
            </div>
          )}

          {explanation.performance_hints.length > 0 && (
            <div className="p-2 rounded bg-amber-50 border border-amber-200">
              <p className="text-xs font-medium text-amber-700 mb-1">Performance Hints:</p>
              <ul className="list-disc list-inside text-amber-600 text-xs space-y-0.5">
                {explanation.performance_hints.map((hint, i) => (
                  <li key={i}>{hint}</li>
                ))}
              </ul>
            </div>
          )}

          {explanation.security_notes.length > 0 && (
            <div className="p-2 rounded bg-red-50 border border-red-200">
              <p className="text-xs font-medium text-red-700 mb-1">Security Notes:</p>
              <ul className="list-disc list-inside text-red-600 text-xs space-y-0.5">
                {explanation.security_notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function DatabaseQueryBuilder({
  onExecute,
  onCopy,
  initialQuery = '',
  initialDbType = 'postgresql',
  className,
}: DatabaseQueryBuilderProps) {
  const [query, setQuery] = React.useState(initialQuery);
  const [dbType, setDbType] = React.useState<DatabaseType>(initialDbType);
  const [validation, setValidation] = React.useState<ValidationResult | null>(null);
  const [explanation, setExplanation] = React.useState<QueryExplanation | null>(null);
  const [isValidating, setIsValidating] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  const handleValidate = React.useCallback(async () => {
    if (!query.trim()) return;

    setIsValidating(true);
    try {
      // Call validation API
      const response = await fetch('/api/database/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, database_type: dbType }),
      });

      if (response.ok) {
        const data = await response.json();
        setValidation(data);
      }

      // Call explain API
      const explainResponse = await fetch('/api/database/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, database_type: dbType }),
      });

      if (explainResponse.ok) {
        const explainData = await explainResponse.json();
        setExplanation(explainData);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setIsValidating(false);
    }
  }, [query, dbType]);

  const handleCopy = React.useCallback(() => {
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.(query);
  }, [query, onCopy]);

  const handleExecute = React.useCallback(() => {
    onExecute?.(query, dbType);
  }, [query, dbType, onExecute]);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <Database className="h-5 w-5 text-muted-foreground" />
        <h3 className="font-medium">Query Builder</h3>

        <select
          value={dbType}
          onChange={(e) => setDbType(e.target.value as DatabaseType)}
          className="ml-auto text-sm rounded-md border bg-background px-2 py-1"
        >
          {databaseOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.icon} {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Query Input */}
      <div className="flex-1 min-h-0 mb-4">
        <textarea
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setValidation(null);
            setExplanation(null);
          }}
          placeholder={
            dbType === 'mongodb'
              ? 'db.collection.find({ field: "value" })'
              : 'SELECT * FROM table_name WHERE condition;'
          }
          className={cn(
            'w-full h-full min-h-[150px] p-3 rounded-lg border bg-background',
            'font-mono text-sm resize-none',
            'focus:outline-none focus:ring-2 focus:ring-primary'
          )}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mb-4">
        <button
          onClick={handleValidate}
          disabled={!query.trim() || isValidating}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm',
            'bg-primary text-primary-foreground',
            'hover:bg-primary/90 disabled:opacity-50'
          )}
        >
          <FileCode className="h-4 w-4" />
          {isValidating ? 'Analyzing...' : 'Analyze Query'}
        </button>

        <button
          onClick={handleCopy}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm',
            'border bg-background hover:bg-muted'
          )}
        >
          <Copy className="h-4 w-4" />
          {copied ? 'Copied!' : 'Copy'}
        </button>

        {onExecute && (
          <button
            onClick={handleExecute}
            disabled={!query.trim() || (validation !== null && !validation.is_valid)}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm ml-auto',
              'bg-green-600 text-white',
              'hover:bg-green-700 disabled:opacity-50'
            )}
          >
            <Play className="h-4 w-4" />
            Execute
          </button>
        )}
      </div>

      {/* Results */}
      <div className="space-y-3">
        {validation && <ValidationPanel validation={validation} />}
        {explanation && <ExplanationPanel explanation={explanation} />}
      </div>
    </div>
  );
}

export default DatabaseQueryBuilder;
