'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Info,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from 'lucide-react';

export interface Vulnerability {
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  message: string;
  line?: number;
  column?: number;
  code_snippet?: string;
  fix_suggestion?: string;
  cwe_id?: string;
  owasp_category?: string;
}

export interface ScanResult {
  passed: boolean;
  vulnerabilities: Vulnerability[];
  risk_score: number;
  scan_duration_ms: number;
  scanner_used: string;
  blocked: boolean;
  summary: string;
  counts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}

interface SecurityReportProps {
  result: ScanResult;
  className?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

const severityConfig = {
  critical: {
    icon: ShieldX,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-950',
    border: 'border-red-200 dark:border-red-800',
    badge: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  },
  high: {
    icon: ShieldAlert,
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-950',
    border: 'border-orange-200 dark:border-orange-800',
    badge: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-950',
    border: 'border-yellow-200 dark:border-yellow-800',
    badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  },
  low: {
    icon: Shield,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-950',
    border: 'border-blue-200 dark:border-blue-800',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  },
  info: {
    icon: Info,
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-950',
    border: 'border-gray-200 dark:border-gray-800',
    badge: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
  },
};

function VulnerabilityItem({ vuln }: { vuln: Vulnerability }) {
  const [expanded, setExpanded] = React.useState(false);
  const config = severityConfig[vuln.severity];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'rounded-lg border p-3',
        config.bg,
        config.border
      )}
    >
      <div
        className="flex items-start gap-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <Icon className={cn('h-5 w-5 mt-0.5 flex-shrink-0', config.color)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={cn('text-xs font-medium px-2 py-0.5 rounded', config.badge)}>
              {vuln.severity.toUpperCase()}
            </span>
            <span className="text-xs text-muted-foreground">
              {vuln.type.replace(/_/g, ' ')}
            </span>
            {vuln.line && (
              <span className="text-xs text-muted-foreground">
                Line {vuln.line}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm font-medium">{vuln.message}</p>
        </div>
        {(vuln.fix_suggestion || vuln.code_snippet || vuln.cwe_id) && (
          <button className="p-1 hover:bg-black/5 dark:hover:bg-white/5 rounded">
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        )}
      </div>

      {expanded && (
        <div className="mt-3 pl-8 space-y-2">
          {vuln.code_snippet && (
            <div className="rounded bg-black/5 dark:bg-white/5 p-2">
              <code className="text-xs font-mono break-all">{vuln.code_snippet}</code>
            </div>
          )}
          {vuln.fix_suggestion && (
            <div className="text-sm">
              <span className="font-medium text-green-600 dark:text-green-400">
                Fix:{' '}
              </span>
              {vuln.fix_suggestion}
            </div>
          )}
          <div className="flex gap-3 text-xs text-muted-foreground">
            {vuln.cwe_id && (
              <a
                href={`https://cwe.mitre.org/data/definitions/${vuln.cwe_id.replace('CWE-', '')}.html`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 hover:text-foreground"
              >
                {vuln.cwe_id}
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {vuln.owasp_category && (
              <span>{vuln.owasp_category}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function RiskMeter({ score }: { score: number }) {
  const getColor = () => {
    if (score >= 75) return 'bg-red-500';
    if (score >= 50) return 'bg-orange-500';
    if (score >= 25) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">Risk Score</span>
        <span className="font-medium">{score}/100</span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', getColor())}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

function SeverityCounts({ counts }: { counts: ScanResult['counts'] }) {
  const items = [
    { key: 'critical', label: 'Critical', count: counts.critical },
    { key: 'high', label: 'High', count: counts.high },
    { key: 'medium', label: 'Medium', count: counts.medium },
    { key: 'low', label: 'Low', count: counts.low },
    { key: 'info', label: 'Info', count: counts.info },
  ];

  return (
    <div className="flex gap-2 flex-wrap">
      {items
        .filter((item) => item.count > 0)
        .map((item) => {
          const config = severityConfig[item.key as keyof typeof severityConfig];
          return (
            <span
              key={item.key}
              className={cn('text-xs font-medium px-2 py-1 rounded', config.badge)}
            >
              {item.count} {item.label}
            </span>
          );
        })}
    </div>
  );
}

export function SecurityReport({
  result,
  className,
  collapsible = false,
  defaultExpanded = true,
}: SecurityReportProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  const Header = () => (
    <div
      className={cn(
        'flex items-center justify-between',
        collapsible && 'cursor-pointer'
      )}
      onClick={() => collapsible && setExpanded(!expanded)}
    >
      <div className="flex items-center gap-3">
        {result.passed ? (
          <ShieldCheck className="h-6 w-6 text-green-500" />
        ) : (
          <ShieldAlert className="h-6 w-6 text-red-500" />
        )}
        <div>
          <h3 className="font-semibold">
            {result.passed ? 'Security Check Passed' : 'Security Issues Found'}
          </h3>
          <p className="text-sm text-muted-foreground">{result.summary}</p>
        </div>
      </div>
      {collapsible && (
        <button className="p-2 hover:bg-muted rounded">
          {expanded ? (
            <ChevronUp className="h-5 w-5" />
          ) : (
            <ChevronDown className="h-5 w-5" />
          )}
        </button>
      )}
    </div>
  );

  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-4 space-y-4',
        result.blocked && 'border-red-500',
        className
      )}
    >
      <Header />

      {(!collapsible || expanded) && (
        <>
          {result.blocked && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950 rounded-lg p-3">
              <ShieldX className="h-5 w-5" />
              <span>
                Execution blocked due to high-severity vulnerabilities.
              </span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <RiskMeter score={result.risk_score} />
            <div className="space-y-1">
              <div className="text-xs text-muted-foreground">Scanner</div>
              <div className="text-sm font-medium">{result.scanner_used}</div>
              <div className="text-xs text-muted-foreground">
                {result.scan_duration_ms}ms
              </div>
            </div>
          </div>

          <SeverityCounts counts={result.counts} />

          {result.vulnerabilities.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Vulnerabilities</h4>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {result.vulnerabilities.map((vuln, index) => (
                  <VulnerabilityItem key={index} vuln={vuln} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default SecurityReport;
