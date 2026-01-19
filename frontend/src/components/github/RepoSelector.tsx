'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import {
  GitBranch,
  Lock,
  Globe,
  Star,
  Search,
  RefreshCw,
  ChevronDown,
  Check,
  Loader2,
} from 'lucide-react';
import type { Repository, RepositoryContext } from '@/lib/api/github';

interface RepoSelectorProps {
  repositories: Repository[];
  selectedRepo?: Repository;
  repoContext?: RepositoryContext;
  isLoading?: boolean;
  isAnalyzing?: boolean;
  onSelect: (repo: Repository) => void;
  onAnalyze?: (repo: Repository) => void;
  onRefresh?: () => void;
  className?: string;
}

export function RepoSelector({
  repositories,
  selectedRepo,
  repoContext,
  isLoading = false,
  isAnalyzing = false,
  onSelect,
  onAnalyze,
  onRefresh,
  className,
}: RepoSelectorProps) {
  const [search, setSearch] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);

  const filteredRepos = React.useMemo(() => {
    if (!search) return repositories;
    const lowerSearch = search.toLowerCase();
    return repositories.filter(
      (repo) =>
        repo.name.toLowerCase().includes(lowerSearch) ||
        repo.full_name.toLowerCase().includes(lowerSearch) ||
        repo.description?.toLowerCase().includes(lowerSearch)
    );
  }, [repositories, search]);

  const handleSelect = (repo: Repository) => {
    onSelect(repo);
    setIsOpen(false);
    setSearch('');
  };

  return (
    <div className={cn('relative', className)}>
      {/* Selected Repository Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className={cn(
          'w-full flex items-center gap-2 px-3 py-2 rounded-lg border',
          'bg-background hover:bg-muted/50 transition-colors',
          'text-left text-sm',
          isOpen && 'ring-2 ring-primary'
        )}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <GitBranch className="h-4 w-4 text-muted-foreground" />
        )}

        <span className="flex-1 truncate">
          {selectedRepo ? (
            <span className="flex items-center gap-1">
              {selectedRepo.private ? (
                <Lock className="h-3 w-3 text-amber-500" />
              ) : (
                <Globe className="h-3 w-3 text-green-500" />
              )}
              {selectedRepo.full_name}
            </span>
          ) : (
            <span className="text-muted-foreground">Select a repository...</span>
          )}
        </span>

        <ChevronDown
          className={cn(
            'h-4 w-4 text-muted-foreground transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </button>

      {/* Repository Context Info */}
      {selectedRepo && repoContext && (
        <div className="mt-2 p-2 rounded-lg bg-muted/50 text-xs space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            {repoContext.primary_language && (
              <span className="px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                {repoContext.primary_language}
              </span>
            )}
            {repoContext.framework_detected && (
              <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                {repoContext.framework_detected}
              </span>
            )}
            {repoContext.package_manager && (
              <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-700">
                {repoContext.package_manager}
              </span>
            )}
          </div>
          {repoContext.patterns.length > 0 && (
            <p className="text-muted-foreground">
              {repoContext.patterns.slice(0, 3).join(' · ')}
            </p>
          )}
        </div>
      )}

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border bg-popover shadow-lg">
          {/* Search Input */}
          <div className="p-2 border-b">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search repositories..."
                className="w-full pl-8 pr-3 py-1.5 text-sm rounded border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                autoFocus
              />
            </div>
          </div>

          {/* Repository List */}
          <div className="max-h-64 overflow-y-auto">
            {filteredRepos.length === 0 ? (
              <div className="p-4 text-center text-sm text-muted-foreground">
                {search ? 'No repositories found' : 'No repositories available'}
              </div>
            ) : (
              filteredRepos.map((repo) => (
                <button
                  key={repo.id}
                  onClick={() => handleSelect(repo)}
                  className={cn(
                    'w-full flex items-start gap-2 px-3 py-2 text-left',
                    'hover:bg-muted/50 transition-colors',
                    selectedRepo?.id === repo.id && 'bg-muted'
                  )}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {repo.private ? (
                      <Lock className="h-4 w-4 text-amber-500" />
                    ) : (
                      <Globe className="h-4 w-4 text-green-500" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">
                        {repo.full_name}
                      </span>
                      {selectedRepo?.id === repo.id && (
                        <Check className="h-4 w-4 text-primary flex-shrink-0" />
                      )}
                    </div>
                    {repo.description && (
                      <p className="text-xs text-muted-foreground truncate">
                        {repo.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      {repo.language && <span>{repo.language}</span>}
                      <span className="flex items-center gap-0.5">
                        <Star className="h-3 w-3" />
                        {repo.stargazers_count}
                      </span>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Actions */}
          <div className="p-2 border-t flex items-center justify-between">
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isLoading}
                className="flex items-center gap-1 px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className={cn('h-3 w-3', isLoading && 'animate-spin')} />
                Refresh
              </button>
            )}
            {onAnalyze && selectedRepo && (
              <button
                onClick={() => onAnalyze(selectedRepo)}
                disabled={isAnalyzing}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                {isAnalyzing ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <GitBranch className="h-3 w-3" />
                )}
                Analyze
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default RepoSelector;
