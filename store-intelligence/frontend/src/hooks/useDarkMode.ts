import { useEffect, useState } from 'react';

const STORAGE_KEY = 'purplle-dashboard-theme';

export function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === 'undefined') {
      return false;
    }
    return localStorage.getItem(STORAGE_KEY) === 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
      localStorage.setItem(STORAGE_KEY, 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem(STORAGE_KEY, 'light');
    }
  }, [darkMode]);

  return { darkMode, setDarkMode };
}
