'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  Server,
  Plus,
  Trash2,
  Copy,
  ExternalLink,
  Play,
  Square,
  Clock,
  Activity,
  ChevronDown,
  ChevronUp,
  Edit2,
} from 'lucide-react';

export interface MockEndpoint {
  method: string;
  path: string;
  response_body: any;
  status_code: number;
  headers: Record<string, string>;
  delay_ms: number;
  description?: string;
}

export interface MockServer {
  id: string;
  user_id: string;
  name: string;
  endpoints: MockEndpoint[];
  status: 'starting' | 'running' | 'stopped' | 'error';
  port?: number;
  url?: string;
  session_id?: string;
  spec_type?: string;
  created_at: string;
  expires_at?: string;
  request_count: number;
  error_message?: string;
}

interface MockServerManagerProps {
  mocks: MockServer[];
  onCreateMock?: () => void;
  onDeleteMock?: (mockId: string) => void;
  onStopMock?: (mockId: string) => void;
  onViewLogs?: (mockId: string) => void;
  isLoading?: boolean;
  className?: string;
}

const methodColors: Record<string, string> = {
  GET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  POST: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  PUT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  PATCH: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  DELETE: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  HEAD: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  OPTIONS: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

const statusConfig = {
  starting: {
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-100 dark:bg-yellow-900',
    label: 'Starting',
  },
  running: {
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900',
    label: 'Running',
  },
  stopped: {
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-100 dark:bg-gray-900',
    label: 'Stopped',
  },
  error: {
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900',
    label: 'Error',
  },
};

function EndpointBadge({ endpoint }: { endpoint: MockEndpoint }) {
  const colorClass = methodColors[endpoint.method] || methodColors.GET;

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className={cn('px-2 py-0.5 rounded text-xs font-bold', colorClass)}>
        {endpoint.method}
      </span>
      <span className="font-mono text-muted-foreground">{endpoint.path}</span>
      <span className="text-xs text-muted-foreground">
        {endpoint.status_code}
      </span>
    </div>
  );
}

function MockServerCard({
  mock,
  onDelete,
  onStop,
  onViewLogs,
}: {
  mock: MockServer;
  onDelete?: () => void;
  onStop?: () => void;
  onViewLogs?: () => void;
}) {
  const [expanded, setExpanded] = React.useState(false);
  const status = statusConfig[mock.status];

  const copyUrl = () => {
    if (mock.url) {
      navigator.clipboard.writeText(mock.url);
    }
  };

  const getTimeRemaining = () => {
    if (!mock.expires_at) return null;
    const expires = new Date(mock.expires_at);
    const now = new Date();
    const diff = expires.getTime() - now.getTime();
    if (diff <= 0) return 'Expired';
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes}m`;
    return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
  };

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Server className="h-5 w-5 text-muted-foreground" />
          <div>
            <h3 className="font-medium">{mock.name}</h3>
            <div className="flex items-center gap-2 text-sm">
              <span className={cn('px-2 py-0.5 rounded text-xs', status.bg, status.color)}>
                {status.label}
              </span>
              {mock.port && (
                <span className="text-muted-foreground">Port {mock.port}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {mock.status === 'running' && (
            <button
              onClick={onStop}
              className="p-1.5 hover:bg-muted rounded"
              title="Stop"
            >
              <Square className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={onDelete}
            className="p-1.5 hover:bg-muted rounded text-red-500"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* URL */}
      {mock.url && (
        <div className="flex items-center gap-2 bg-muted/50 rounded p-2">
          <code className="text-sm flex-1 truncate">{mock.url}</code>
          <button
            onClick={copyUrl}
            className="p-1 hover:bg-muted rounded"
            title="Copy URL"
          >
            <Copy className="h-4 w-4" />
          </button>
          <a
            href={mock.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:bg-muted rounded"
            title="Open in new tab"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <Activity className="h-4 w-4" />
          {mock.request_count} requests
        </div>
        {getTimeRemaining() && (
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {getTimeRemaining()}
          </div>
        )}
        <div>{mock.endpoints.length} endpoints</div>
      </div>

      {/* Error */}
      {mock.error_message && (
        <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 rounded p-2">
          {mock.error_message}
        </div>
      )}

      {/* Endpoints */}
      <div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          {expanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
          {expanded ? 'Hide' : 'Show'} endpoints
        </button>

        {expanded && (
          <div className="mt-2 space-y-1.5 pl-4 border-l-2 border-muted">
            {mock.endpoints.map((endpoint, index) => (
              <EndpointBadge key={index} endpoint={endpoint} />
            ))}
          </div>
        )}
      </div>

      {/* View Logs */}
      {onViewLogs && mock.status === 'running' && (
        <button
          onClick={onViewLogs}
          className="w-full text-sm text-muted-foreground hover:text-foreground py-2 border-t"
        >
          View Request Logs
        </button>
      )}
    </div>
  );
}

export function MockServerManager({
  mocks,
  onCreateMock,
  onDeleteMock,
  onStopMock,
  onViewLogs,
  isLoading,
  className,
}: MockServerManagerProps) {
  const runningMocks = mocks.filter((m) => m.status === 'running');
  const otherMocks = mocks.filter((m) => m.status !== 'running');

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Mock Servers</h2>
          <p className="text-sm text-muted-foreground">
            {runningMocks.length} running, {mocks.length} total
          </p>
        </div>
        {onCreateMock && (
          <button
            onClick={onCreateMock}
            className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Mock
          </button>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <Server className="h-5 w-5 animate-pulse mr-2" />
          Loading mocks...
        </div>
      )}

      {/* Empty State */}
      {!isLoading && mocks.length === 0 && (
        <div className="text-center py-8 border rounded-lg bg-muted/20">
          <Server className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
          <h3 className="font-medium mb-1">No Mock Servers</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Create a mock server to test your API integrations
          </p>
          {onCreateMock && (
            <button
              onClick={onCreateMock}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" />
              Create Mock Server
            </button>
          )}
        </div>
      )}

      {/* Running Mocks */}
      {runningMocks.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Play className="h-4 w-4 text-green-500" />
            Running
          </h3>
          <div className="grid gap-3">
            {runningMocks.map((mock) => (
              <MockServerCard
                key={mock.id}
                mock={mock}
                onDelete={() => onDeleteMock?.(mock.id)}
                onStop={() => onStopMock?.(mock.id)}
                onViewLogs={() => onViewLogs?.(mock.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Other Mocks */}
      {otherMocks.length > 0 && (
        <div className="space-y-3">
          {runningMocks.length > 0 && (
            <h3 className="text-sm font-medium text-muted-foreground">
              Other
            </h3>
          )}
          <div className="grid gap-3">
            {otherMocks.map((mock) => (
              <MockServerCard
                key={mock.id}
                mock={mock}
                onDelete={() => onDeleteMock?.(mock.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default MockServerManager;
