"use client";

import { useCallback, useEffect, useRef } from "react";

type ModifierKey = "ctrl" | "meta" | "alt" | "shift";
type KeyHandler = (event: KeyboardEvent) => void;

interface ShortcutConfig {
  key: string;
  modifiers?: ModifierKey[];
  handler: KeyHandler;
  description?: string;
  preventDefault?: boolean;
  enabled?: boolean;
}

interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
  scope?: string;
}

/**
 * Hook for handling keyboard shortcuts.
 *
 * @example
 * useKeyboardShortcuts([
 *   {
 *     key: "k",
 *     modifiers: ["ctrl"],
 *     handler: () => setSearchOpen(true),
 *     description: "Open search",
 *   },
 *   {
 *     key: "Escape",
 *     handler: () => setSearchOpen(false),
 *     description: "Close search",
 *   },
 * ]);
 */
export function useKeyboardShortcuts(
  shortcuts: ShortcutConfig[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enabled = true, scope } = options;
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Skip if target is an input or textarea (unless specifically handled)
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      for (const shortcut of shortcutsRef.current) {
        if (shortcut.enabled === false) continue;

        // Check if key matches
        const keyMatches =
          event.key.toLowerCase() === shortcut.key.toLowerCase() ||
          event.code.toLowerCase() === shortcut.key.toLowerCase();

        if (!keyMatches) continue;

        // Check modifiers
        const modifiers = shortcut.modifiers || [];
        const ctrlRequired = modifiers.includes("ctrl");
        const metaRequired = modifiers.includes("meta");
        const altRequired = modifiers.includes("alt");
        const shiftRequired = modifiers.includes("shift");

        // Check if modifiers match
        const ctrlMatches = ctrlRequired === (event.ctrlKey || event.metaKey);
        const altMatches = altRequired === event.altKey;
        const shiftMatches = shiftRequired === event.shiftKey;

        // For shortcuts without modifiers, skip if typing in input
        if (!ctrlRequired && !metaRequired && !altRequired && isInput) {
          continue;
        }

        if (ctrlMatches && altMatches && shiftMatches) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }
          shortcut.handler(event);
          return;
        }
      }
    },
    [enabled]
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled, handleKeyDown]);
}

/**
 * Get a list of all registered shortcuts for display.
 */
export function getShortcutDisplayString(shortcut: ShortcutConfig): string {
  const parts: string[] = [];

  if (shortcut.modifiers?.includes("ctrl")) {
    parts.push(navigator.platform.includes("Mac") ? "⌘" : "Ctrl");
  }
  if (shortcut.modifiers?.includes("alt")) {
    parts.push(navigator.platform.includes("Mac") ? "⌥" : "Alt");
  }
  if (shortcut.modifiers?.includes("shift")) {
    parts.push("⇧");
  }

  // Format key nicely
  let keyDisplay = shortcut.key;
  if (shortcut.key === "Escape") keyDisplay = "Esc";
  if (shortcut.key === "Enter") keyDisplay = "↵";
  if (shortcut.key === "ArrowUp") keyDisplay = "↑";
  if (shortcut.key === "ArrowDown") keyDisplay = "↓";
  if (shortcut.key === "ArrowLeft") keyDisplay = "←";
  if (shortcut.key === "ArrowRight") keyDisplay = "→";

  parts.push(keyDisplay.toUpperCase());

  return parts.join(" + ");
}

/**
 * Common keyboard shortcuts for the application.
 */
export const COMMON_SHORTCUTS = {
  SEARCH: { key: "k", modifiers: ["ctrl"] as ModifierKey[] },
  NEW_CHAT: { key: "n", modifiers: ["ctrl"] as ModifierKey[] },
  SEND_MESSAGE: { key: "Enter", modifiers: ["ctrl"] as ModifierKey[] },
  CLOSE: { key: "Escape" },
  COPY: { key: "c", modifiers: ["ctrl"] as ModifierKey[] },
  PASTE: { key: "v", modifiers: ["ctrl"] as ModifierKey[] },
  SAVE: { key: "s", modifiers: ["ctrl"] as ModifierKey[] },
  UNDO: { key: "z", modifiers: ["ctrl"] as ModifierKey[] },
  REDO: { key: "z", modifiers: ["ctrl", "shift"] as ModifierKey[] },
};
