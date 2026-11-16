import { create } from "zustand";

export type Theme = "system" | "light" | "dark";
const KEY = "govsim.theme";

function load(): Theme {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

export function isDark(theme: Theme): boolean {
  if (theme === "system")
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  return theme === "dark";
}

export function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", isDark(theme));
}

interface UiState {
  theme: Theme;
  setTheme: (t: Theme) => void;
}

export const useUi = create<UiState>((set) => ({
  theme: load(),
  setTheme: (theme) => {
    try {
      if (theme === "system") localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, theme);
    } catch {
      // storage can be blocked; the choice then lasts for this visit only
    }
    applyTheme(theme);
    set({ theme });
  },
}));
