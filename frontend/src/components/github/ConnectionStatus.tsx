'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  Github,
  CheckCircle,
  XCircle,
  ExternalLink,
  LogOut,
  Loader2,
  Shield,
} from 'lucide-react';
import type { GitHubConnectionStatus } from '@/lib/api/github';

interface ConnectionStatusProps {
  status: GitHubConnectionStatus | null;
  isLoading?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  className?: string;
}

export function ConnectionStatus({
  status,
  isLoading = false,
  onConnect,
  onDisconnect,
  className,
}: ConnectionStatusProps) {
  const isConnected = status?.connected ?? false;

  return (
    <div
      className={cn(
        'rounded-lg border p-4',
        isConnected ? 'bg-green-50 border-green-200' : 'bg-muted/50',
        className
      )}
    >
      <div className="flex items-start gap-4">
        {/* GitHub Icon with Status */}
        <div className="relative">
          <div
            className={cn(
              'p-3 rounded-full',
              isConnected ? 'bg-green-100' : 'bg-muted'
            )}
          >
            <Github className="h-6 w-6" />
          </div>
          {isConnected && (
            <CheckCircle className="absolute -bottom-1 -right-1 h-5 w-5 text-green-500 bg-white rounded-full" />
          )}
        </div>

        {/* Connection Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-medium">GitHub</h3>
            {isConnected ? (
              <span className="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">
                Connected
              </span>
            ) : (
              <span className="px-2 py-0.5 text-xs rounded-full bg-muted text-muted-foreground">
                Not connected
              </span>
            )}
          </div>

          {isConnected && status ? (
            <div className="space-y-2">
              {/* User Info */}
              <div className="flex items-center gap-2">
                {status.avatar_url && (
                  <img
                    src={status.avatar_url}
                    alt={status.username}
                    className="h-6 w-6 rounded-full"
                  />
                )}
                <span className="text-sm font-medium">{status.username}</span>
                <a
                  href={`https://github.com/${status.username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>

              {/* Scopes */}
              {status.scopes.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  <Shield className="h-3 w-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Scopes:</span>
                  {status.scopes.map((scope) => (
                    <span
                      key={scope}
                      className="px-1.5 py-0.5 text-xs rounded bg-white border"
                    >
                      {scope}
                    </span>
                  ))}
                </div>
              )}

              {/* Connected At */}
              {status.connected_at && (
                <p className="text-xs text-muted-foreground">
                  Connected {new Date(status.connected_at).toLocaleDateString()}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Connect your GitHub account to access repositories for code context and generation.
            </p>
          )}
        </div>

        {/* Actions */}
        <div>
          {isConnected ? (
            <button
              onClick={onDisconnect}
              disabled={isLoading}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm',
                'border border-red-200 text-red-600',
                'hover:bg-red-50 disabled:opacity-50'
              )}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <LogOut className="h-4 w-4" />
              )}
              Disconnect
            </button>
          ) : (
            <button
              onClick={onConnect}
              disabled={isLoading}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm',
                'bg-[#24292e] text-white',
                'hover:bg-[#2f363d] disabled:opacity-50'
              )}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Github className="h-4 w-4" />
              )}
              Connect GitHub
            </button>
          )}
        </div>
      </div>

      {/* Features List */}
      {!isConnected && (
        <div className="mt-4 pt-4 border-t">
          <h4 className="text-sm font-medium mb-2">With GitHub connected, you can:</h4>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Access your repositories for code context
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Analyze project structure and frameworks
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Generate code that matches your project style
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Read existing files for context
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}

export default ConnectionStatus;
