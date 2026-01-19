'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  Award,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Code2,
  FileText,
  TestTube,
  Sparkles,
  Shield,
  ChevronDown,
  ChevronUp,
  Lightbulb,
} from 'lucide-react';

export interface ComplexityMetrics {
  lines_of_code: number;
  function_count: number;
  class_count: number;
  max_nesting_depth: number;
  avg_function_length: number;
  cyclomatic_complexity: number;
}

export interface DocumentationMetrics {
  has_module_docstring: boolean;
  function_docstrings: number;
  total_functions: number;
  class_docstrings: number;
  total_classes: number;
  inline_comments: number;
  docstring_coverage: number;
}

export interface TestMetrics {
  has_tests: boolean;
  test_count: number;
  assertion_count: number;
  estimated_coverage: number;
}

export interface QualityScoreData {
  overall_score: number;
  level: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  complexity: ComplexityMetrics;
  documentation: DocumentationMetrics;
  tests: TestMetrics;
  lint_score: number;
  security_score: number;
  breakdown: {
    complexity: number;
    documentation: number;
    tests: number;
    lint: number;
    security: number;
  };
  recommendations: string[];
}

interface QualityScoreProps {
  score: QualityScoreData;
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

const levelConfig = {
  excellent: {
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-950',
    border: 'border-green-200 dark:border-green-800',
    icon: Award,
    label: 'Excellent',
  },
  good: {
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-950',
    border: 'border-blue-200 dark:border-blue-800',
    icon: CheckCircle2,
    label: 'Good',
  },
  fair: {
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-950',
    border: 'border-yellow-200 dark:border-yellow-800',
    icon: TrendingUp,
    label: 'Fair',
  },
  poor: {
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-950',
    border: 'border-orange-200 dark:border-orange-800',
    icon: TrendingDown,
    label: 'Poor',
  },
  critical: {
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-950',
    border: 'border-red-200 dark:border-red-800',
    icon: AlertCircle,
    label: 'Critical',
  },
};

function ScoreRing({
  score,
  size = 80,
  strokeWidth = 8,
}: {
  score: number;
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-blue-500';
    if (score >= 50) return 'text-yellow-500';
    if (score >= 30) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className="stroke-muted fill-none"
        />
        {/* Score circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className={cn('fill-none stroke-current transition-all duration-500', getColor())}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xl font-bold">{score}</span>
      </div>
    </div>
  );
}

function ScoreBar({
  label,
  score,
  icon: Icon,
}: {
  label: string;
  score: number;
  icon: React.ElementType;
}) {
  const getBarColor = () => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-1.5">
          <Icon className="h-3.5 w-3.5 text-muted-foreground" />
          <span>{label}</span>
        </div>
        <span className="font-medium">{score}</span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', getBarColor())}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

function MetricItem({
  label,
  value,
  suffix,
}: {
  label: string;
  value: number | string | boolean;
  suffix?: string;
}) {
  const displayValue = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value;

  return (
    <div className="flex justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">
        {displayValue}
        {suffix && <span className="text-muted-foreground ml-0.5">{suffix}</span>}
      </span>
    </div>
  );
}

export function QualityScore({
  score,
  className,
  showDetails = true,
  compact = false,
}: QualityScoreProps) {
  const [expanded, setExpanded] = React.useState(false);
  const config = levelConfig[score.level];
  const LevelIcon = config.icon;

  if (compact) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-lg border',
          config.bg,
          config.border,
          className
        )}
      >
        <ScoreRing score={score.overall_score} size={36} strokeWidth={4} />
        <div>
          <div className={cn('text-sm font-medium', config.color)}>
            {config.label}
          </div>
          <div className="text-xs text-muted-foreground">Quality Score</div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('rounded-lg border bg-card', className)}>
      {/* Header */}
      <div className="p-4 flex items-center gap-4">
        <ScoreRing score={score.overall_score} />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <LevelIcon className={cn('h-5 w-5', config.color)} />
            <h3 className={cn('font-semibold', config.color)}>{config.label}</h3>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Code Quality Score: {score.overall_score}/100
          </p>
        </div>
      </div>

      {/* Score breakdown */}
      {showDetails && (
        <div className="px-4 pb-4 space-y-3">
          <ScoreBar
            label="Complexity"
            score={score.breakdown.complexity}
            icon={Code2}
          />
          <ScoreBar
            label="Documentation"
            score={score.breakdown.documentation}
            icon={FileText}
          />
          <ScoreBar
            label="Tests"
            score={score.breakdown.tests}
            icon={TestTube}
          />
          <ScoreBar
            label="Lint"
            score={score.breakdown.lint}
            icon={Sparkles}
          />
          <ScoreBar
            label="Security"
            score={score.breakdown.security}
            icon={Shield}
          />
        </div>
      )}

      {/* Expandable details */}
      {showDetails && (
        <div className="border-t">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full px-4 py-2 flex items-center justify-between text-sm text-muted-foreground hover:bg-muted/50"
          >
            <span>Detailed Metrics</span>
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>

          {expanded && (
            <div className="px-4 pb-4 space-y-4">
              {/* Complexity metrics */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-1.5">
                  <Code2 className="h-4 w-4" />
                  Complexity
                </h4>
                <div className="pl-5 space-y-1">
                  <MetricItem label="Lines of Code" value={score.complexity.lines_of_code} />
                  <MetricItem label="Functions" value={score.complexity.function_count} />
                  <MetricItem label="Classes" value={score.complexity.class_count} />
                  <MetricItem label="Max Nesting" value={score.complexity.max_nesting_depth} />
                  <MetricItem
                    label="Avg Function Length"
                    value={score.complexity.avg_function_length}
                    suffix="lines"
                  />
                  <MetricItem
                    label="Cyclomatic Complexity"
                    value={score.complexity.cyclomatic_complexity}
                  />
                </div>
              </div>

              {/* Documentation metrics */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-1.5">
                  <FileText className="h-4 w-4" />
                  Documentation
                </h4>
                <div className="pl-5 space-y-1">
                  <MetricItem label="Module Docstring" value={score.documentation.has_module_docstring} />
                  <MetricItem
                    label="Function Docstrings"
                    value={`${score.documentation.function_docstrings}/${score.documentation.total_functions}`}
                  />
                  <MetricItem
                    label="Docstring Coverage"
                    value={score.documentation.docstring_coverage}
                    suffix="%"
                  />
                  <MetricItem label="Inline Comments" value={score.documentation.inline_comments} />
                </div>
              </div>

              {/* Test metrics */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-1.5">
                  <TestTube className="h-4 w-4" />
                  Tests
                </h4>
                <div className="pl-5 space-y-1">
                  <MetricItem label="Has Tests" value={score.tests.has_tests} />
                  <MetricItem label="Test Count" value={score.tests.test_count} />
                  <MetricItem label="Assertions" value={score.tests.assertion_count} />
                  <MetricItem
                    label="Est. Coverage"
                    value={score.tests.estimated_coverage}
                    suffix="%"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recommendations */}
      {score.recommendations.length > 0 && (
        <div className="border-t px-4 py-3 bg-muted/30">
          <h4 className="text-sm font-medium flex items-center gap-1.5 mb-2">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            Recommendations
          </h4>
          <ul className="space-y-1.5">
            {score.recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="text-xs mt-1">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default QualityScore;
