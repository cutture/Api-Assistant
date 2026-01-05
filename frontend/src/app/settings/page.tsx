/**
 * Settings page - Comprehensive application settings
 */

"use client";

import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { useSettingsStore } from "@/stores/settingsStore";
import { useToast } from "@/hooks/use-toast";
import { Settings, Database, Search, Palette, Clock, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useSettingsStore();
  const { toast } = useToast();

  const handleReset = () => {
    resetSettings();
    toast({
      title: "Settings Reset",
      description: "All settings have been reset to defaults",
    });
  };

  return (
    <MainLayout showSidebar={false}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
            <p className="text-muted-foreground mt-2">
              Configure your preferences and defaults
            </p>
          </div>
          <Button variant="outline" onClick={handleReset}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset All
          </Button>
        </div>

        {/* LLM Provider Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5" />
              <CardTitle>LLM Provider</CardTitle>
            </div>
            <CardDescription>
              Configure your Language Model provider (Ollama or Groq)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="llm-provider">Provider</Label>
              <Select
                value={settings.llmProvider}
                onValueChange={(value: "ollama" | "groq") =>
                  updateSettings({ llmProvider: value })
                }
              >
                <SelectTrigger id="llm-provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ollama">Ollama (Local)</SelectItem>
                  <SelectItem value="groq">Groq (Cloud)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {settings.llmProvider === "ollama" && (
              <div className="space-y-2">
                <Label htmlFor="ollama-url">Ollama Base URL</Label>
                <Input
                  id="ollama-url"
                  type="url"
                  value={settings.ollamaBaseUrl}
                  onChange={(e) => updateSettings({ ollamaBaseUrl: e.target.value })}
                  placeholder="http://localhost:11434"
                />
                <p className="text-xs text-muted-foreground">
                  Default: http://localhost:11434
                </p>
              </div>
            )}

            {settings.llmProvider === "groq" && (
              <div className="space-y-2">
                <Label htmlFor="groq-key">Groq API Key</Label>
                <Input
                  id="groq-key"
                  type="password"
                  value={settings.groqApiKey}
                  onChange={(e) => updateSettings({ groqApiKey: e.target.value })}
                  placeholder="Enter your Groq API key"
                />
                <p className="text-xs text-muted-foreground">
                  Get your API key from{" "}
                  <a
                    href="https://console.groq.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    console.groq.com
                  </a>
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Search Defaults */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Search className="h-5 w-5" />
              <CardTitle>Search Defaults</CardTitle>
            </div>
            <CardDescription>
              Configure default search behavior and features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="search-mode">Default Search Mode</Label>
              <Select
                value={settings.defaultSearchMode}
                onValueChange={(value: "vector" | "hybrid" | "reranked") =>
                  updateSettings({ defaultSearchMode: value })
                }
              >
                <SelectTrigger id="search-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vector">Vector Search</SelectItem>
                  <SelectItem value="hybrid">Hybrid (BM25 + Vector)</SelectItem>
                  <SelectItem value="reranked">Reranked (Best Quality)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="n-results">Default Number of Results</Label>
              <Input
                id="n-results"
                type="number"
                min={1}
                max={100}
                value={settings.defaultNResults}
                onChange={(e) =>
                  updateSettings({ defaultNResults: parseInt(e.target.value, 10) || 10 })
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="use-reranking">Enable Re-ranking</Label>
                <p className="text-sm text-muted-foreground">
                  Use cross-encoder for better result ranking
                </p>
              </div>
              <Switch
                id="use-reranking"
                checked={settings.useReranking}
                onCheckedChange={(checked) => updateSettings({ useReranking: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="use-expansion">Enable Query Expansion</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically expand queries with related terms
                </p>
              </div>
              <Switch
                id="use-expansion"
                checked={settings.useQueryExpansion}
                onCheckedChange={(checked) => updateSettings({ useQueryExpansion: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="use-diversification">Enable Diversification</Label>
                <p className="text-sm text-muted-foreground">
                  Diversify results to reduce redundancy
                </p>
              </div>
              <Switch
                id="use-diversification"
                checked={settings.useDiversification}
                onCheckedChange={(checked) => updateSettings({ useDiversification: checked })}
              />
            </div>
          </CardContent>
        </Card>

        {/* UI Preferences */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Palette className="h-5 w-5" />
              <CardTitle>UI Preferences</CardTitle>
            </div>
            <CardDescription>
              Customize the user interface appearance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <Select
                value={settings.theme}
                onValueChange={(value: "light" | "dark" | "system") =>
                  updateSettings({ theme: value })
                }
              >
                <SelectTrigger id="theme">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="show-scores">Show Relevance Scores</Label>
                <p className="text-sm text-muted-foreground">
                  Display scores in search results
                </p>
              </div>
              <Switch
                id="show-scores"
                checked={settings.showScores}
                onCheckedChange={(checked) => updateSettings({ showScores: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="show-metadata">Show Metadata</Label>
                <p className="text-sm text-muted-foreground">
                  Display document metadata in results
                </p>
              </div>
              <Switch
                id="show-metadata"
                checked={settings.showMetadata}
                onCheckedChange={(checked) => updateSettings({ showMetadata: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-content">Max Content Length</Label>
              <Input
                id="max-content"
                type="number"
                min={100}
                max={2000}
                step={100}
                value={settings.maxContentLength}
                onChange={(e) =>
                  updateSettings({ maxContentLength: parseInt(e.target.value, 10) || 500 })
                }
              />
              <p className="text-xs text-muted-foreground">
                Maximum characters to display per result
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Session Defaults */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <CardTitle>Session Defaults</CardTitle>
            </div>
            <CardDescription>
              Configure default session behavior
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="session-ttl">Default Session TTL (minutes)</Label>
              <Input
                id="session-ttl"
                type="number"
                min={5}
                max={1440}
                value={settings.defaultSessionTtl}
                onChange={(e) =>
                  updateSettings({ defaultSessionTtl: parseInt(e.target.value, 10) || 60 })
                }
              />
              <p className="text-xs text-muted-foreground">
                Time before sessions expire (5-1440 minutes)
              </p>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="auto-cleanup">Enable Auto-Cleanup</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically delete expired sessions
                </p>
              </div>
              <Switch
                id="auto-cleanup"
                checked={settings.enableAutoCleanup}
                onCheckedChange={(checked) => updateSettings({ enableAutoCleanup: checked })}
              />
            </div>
          </CardContent>
        </Card>

        {/* Save indicator */}
        <div className="flex items-center justify-center py-4 text-sm text-muted-foreground">
          <Settings className="h-4 w-4 mr-2" />
          Settings are automatically saved
        </div>
      </div>
    </MainLayout>
  );
}
