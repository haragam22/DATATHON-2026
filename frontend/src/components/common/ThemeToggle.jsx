/**
 * ThemeToggle — switches [data-theme] on <html> between the default
 * control-room navy and the opt-in case-paper light theme (design.md).
 * Persisted to localStorage; defaults to dark (navy) on first visit.
 */

import { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';

const STORAGE_KEY = 'ksp_theme';

export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem(STORAGE_KEY) || 'dark');

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggle = () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));

  return (
    <button
      className="btn-icon"
      onClick={toggle}
      title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-label="Toggle color theme"
      type="button"
    >
      {theme === 'dark' ? <Sun size={16} strokeWidth={1.5} /> : <Moon size={16} strokeWidth={1.5} />}
    </button>
  );
}
