"use client";

import * as React from "react";
import { Moon, Sun, Monitor } from "lucide-react";
import { useSettingsStore } from "@/stores/settingsStore";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { settings, updateSettings } = useSettingsStore();
  const [mounted, setMounted] = React.useState(false);

  // Only render on client-side to avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="sm">
        <Sun className="h-4 w-4" />
      </Button>
    );
  }

  const currentTheme = settings.theme;

  const getIcon = () => {
    switch (currentTheme) {
      case "dark":
        return <Moon className="h-4 w-4" />;
      case "light":
        return <Sun className="h-4 w-4" />;
      case "system":
        return <Monitor className="h-4 w-4" />;
      default:
        return <Sun className="h-4 w-4" />;
    }
  };

  const getNextTheme = () => {
    switch (currentTheme) {
      case "light":
        return "dark";
      case "dark":
        return "system";
      case "system":
        return "light";
      default:
        return "light";
    }
  };

  const getThemeLabel = () => {
    switch (currentTheme) {
      case "dark":
        return "Dark mode";
      case "light":
        return "Light mode";
      case "system":
        return "System mode";
      default:
        return "Toggle theme";
    }
  };

  const toggleTheme = () => {
    updateSettings({ theme: getNextTheme() });
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      title={`Current: ${getThemeLabel()}. Click to change.`}
    >
      {getIcon()}
    </Button>
  );
}
