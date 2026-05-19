import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

interface ThemeData {
  css_variables: Record<string, string>;
  layout?: Record<string, string>;
  name?: string;
}

const CACHE_KEY = 'b2b_active_theme';
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    loadAndApplyTheme();
  }, []);

  const loadAndApplyTheme = async () => {
    try {
      // Check cache
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        if (Date.now() - timestamp < CACHE_TTL) {
          applyTheme(data);
          setLoaded(true);
          // Refresh in background
          refreshTheme();
          return;
        }
      }

      await refreshTheme();
    } catch (e) {
      console.warn('[ThemeProvider] Failed to load theme, using defaults');
    } finally {
      setLoaded(true);
    }
  };

  const refreshTheme = async () => {
    try {
      const data: ThemeData = await apiClient.get('/themes/active');
      applyTheme(data);
      localStorage.setItem(CACHE_KEY, JSON.stringify({ data, timestamp: Date.now() }));
    } catch (e) {
      // Silently fail — use CSS defaults
    }
  };

  const applyTheme = (theme: ThemeData) => {
    const root = document.documentElement;

    // Applique les CSS variables
    Object.entries(theme.css_variables || {}).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });

    // Applique le layout
    if (theme.layout) {
      Object.entries(theme.layout).forEach(([key, value]) => {
        root.style.setProperty(`--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value);
      });
    }

    // Data attribute pour CSS conditionnel
    const isDark = (theme.css_variables['--bg-primary'] || '').includes('0d') ||
                   (theme.css_variables['--bg-primary'] || '').includes('0f1') ||
                   (theme.css_variables['--bg-primary'] || '').startsWith('#0');
    root.setAttribute('data-theme', isDark ? 'dark' : 'light');
  };

  // Expose pour refresh manuel (après activation d'un thème)
  (window as any).__refreshTheme = refreshTheme;

  return <>{children}</>;
}
