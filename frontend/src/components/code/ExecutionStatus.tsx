/**
 * ExecutionStatus Component
 *
 * Displays the status of code execution with progress indicators,
 * validation results, and attempt history.
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  AlertTriangle,
  ChevronDown,
  Terminal,
  FlaskConical,
  Shield,
  FileCode,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";

type ExecutionStatusType = "pending" | "running" | "passed" | "failed" | "partial";

interface ValidationSignal {
  name: string;
  passed: boolean;
  message: string;
}

interface ExecutionAttempt {
  attemptNumber: number;
  status: ExecutionStatusType;
  errorMessage?: string;
  validationSignals: ValidationSignal[];
  executionTimeMs?: number;
}

interface ExecutionStatusProps {
  status: ExecutionStatusType;
  currentAttempt: number;
  maxAttempts: number;
  language: string;
  complexityScore?: number;
  qualityScore?: number;
  llmProvider?: string;
  llmModel?: string;
  testPassed?: boolean;
  lintPassed?: boolean;
  securityPassed?: boolean;
  stdout?: string;
  stderr?: string;
  attempts?: ExecutionAttempt[];
  estimatedTimeSeconds?: number;
  className?: string;
}

export function ExecutionStatus({
  status,
  currentAttempt,
  maxAttempts,
  language,
  complexityScore,
  qualityScore,
  llmProvider,
  llmModel,
  testPassed,
  lintPassed,
  securityPassed,
  stdout,
  stderr,
  attempts = [],
  estimatedTimeSeconds,
  className,
}: ExecutionStatusProps) {
  const [showOutput, setShowOutput] = useState(false);
  const [showAttempts, setShowAttempts] = useState(false);

  const getStatusIcon = (s: ExecutionStatusType) => {
    switch (s) {
      case "passed":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "partial":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case "running":
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = (s: ExecutionStatusType) => {
    switch (s) {
      case "passed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "partial":
        return "bg-yellow-500";
      case "running":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusText = (s: ExecutionStatusType) => {
    switch (s) {
      case "passed":
        return "Passed";
      case "failed":
        return "Failed";
      case "partial":
        return "Partial";
      case "running":
        return "Running";
      default:
        return "Pending";
    }
  };

  const progress = status === "running"
    ? Math.min(((currentAttempt - 1) / maxAttempts) * 100 + 20, 95)
    : status === "passed"
    ? 100
    : status === "failed"
    ? 100
    : 0;

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(status)}
            <CardTitle className="text-lg">Execution Status</CardTitle>
          </div>
          <Badge
            variant="outline"
            className={cn("text-white", getStatusColor(status))}
          >
            {getStatusText(status)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress bar */}
        {status === "running" && (
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>
                Attempt {currentAttempt} of {maxAttempts}
              </span>
              {estimatedTimeSeconds && (
                <span className="text-muted-foreground">
                  Est. {estimatedTimeSeconds}s
                </span>
              )}
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        )}

        {/* Info badges */}
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">
            <FileCode className="mr-1 h-3 w-3" />
            {language}
          </Badge>
          {complexityScore !== undefined && (
            <Badge variant="secondary">
              Complexity: {complexityScore}/10
            </Badge>
          )}
          {qualityScore !== undefined && status !== "running" && (
            <Badge
              variant="secondary"
              className={cn(
                qualityScore >= 8 && "bg-green-100 text-green-800",
                qualityScore >= 5 && qualityScore < 8 && "bg-yellow-100 text-yellow-800",
                qualityScore < 5 && "bg-red-100 text-red-800"
              )}
            >
              Quality: {qualityScore}/10
            </Badge>
          )}
          {llmProvider && (
            <Badge variant="outline">
              {llmProvider}/{llmModel?.split("-")[0]}
            </Badge>
          )}
        </div>

        {/* Validation signals */}
        {(testPassed !== undefined || lintPassed !== undefined || securityPassed !== undefined) && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Validation</h4>
            <div className="grid grid-cols-3 gap-2">
              {testPassed !== undefined && (
                <ValidationBadge
                  icon={<FlaskConical className="h-4 w-4" />}
                  label="Tests"
                  passed={testPassed}
                />
              )}
              {lintPassed !== undefined && (
                <ValidationBadge
                  icon={<FileCode className="h-4 w-4" />}
                  label="Lint"
                  passed={lintPassed}
                />
              )}
              {securityPassed !== undefined && (
                <ValidationBadge
                  icon={<Shield className="h-4 w-4" />}
                  label="Security"
                  passed={securityPassed}
                />
              )}
            </div>
          </div>
        )}

        {/* Output section */}
        {(stdout || stderr) && (
          <Collapsible open={showOutput} onOpenChange={setShowOutput}>
            <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md border p-2 hover:bg-muted/50">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4" />
                <span className="text-sm font-medium">Output</span>
              </div>
              <ChevronDown
                className={cn(
                  "h-4 w-4 transition-transform",
                  showOutput && "rotate-180"
                )}
              />
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2">
              {stdout && (
                <div className="mb-2">
                  <div className="text-xs text-muted-foreground mb-1">stdout</div>
                  <pre className="rounded-md bg-muted p-2 text-xs overflow-x-auto max-h-40">
                    {stdout}
                  </pre>
                </div>
              )}
              {stderr && (
                <div>
                  <div className="text-xs text-red-500 mb-1">stderr</div>
                  <pre className="rounded-md bg-red-50 dark:bg-red-950 p-2 text-xs overflow-x-auto max-h-40 text-red-700 dark:text-red-300">
                    {stderr}
                  </pre>
                </div>
              )}
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Attempts history */}
        {attempts.length > 1 && (
          <Collapsible open={showAttempts} onOpenChange={setShowAttempts}>
            <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md border p-2 hover:bg-muted/50">
              <div className="flex items-center gap-2">
                <RotateCcw className="h-4 w-4" />
                <span className="text-sm font-medium">
                  Attempt History ({attempts.length})
                </span>
              </div>
              <ChevronDown
                className={cn(
                  "h-4 w-4 transition-transform",
                  showAttempts && "rotate-180"
                )}
              />
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-2">
              {attempts.map((attempt) => (
                <div
                  key={attempt.attemptNumber}
                  className="flex items-center justify-between rounded-md border p-2"
                >
                  <div className="flex items-center gap-2">
                    {getStatusIcon(attempt.status)}
                    <span className="text-sm">Attempt {attempt.attemptNumber}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {attempt.executionTimeMs && (
                      <span className="text-xs text-muted-foreground">
                        {attempt.executionTimeMs}ms
                      </span>
                    )}
                    <Badge
                      variant="outline"
                      className={cn("text-xs", getStatusColor(attempt.status))}
                    >
                      {getStatusText(attempt.status)}
                    </Badge>
                  </div>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}

interface ValidationBadgeProps {
  icon: React.ReactNode;
  label: string;
  passed: boolean;
}

function ValidationBadge({ icon, label, passed }: ValidationBadgeProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border p-2",
        passed
          ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950"
          : "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
      )}
    >
      <div className={cn(passed ? "text-green-600" : "text-red-600")}>
        {icon}
      </div>
      <span className="text-sm">{label}</span>
      {passed ? (
        <CheckCircle2 className="h-4 w-4 text-green-600 ml-auto" />
      ) : (
        <XCircle className="h-4 w-4 text-red-600 ml-auto" />
      )}
    </div>
  );
}

export default ExecutionStatus;
