import { useEffect, useState } from 'react';

export function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    // Check for the newer settings format first
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        if (parsedSettings.appearance && 'darkMode' in parsedSettings.appearance) {
          return parsedSettings.appearance.darkMode;
        }
      }
    } catch (error) {
      console.error('Error reading newer settings format:', error);
    }
    
    // Fall back to the old standalone darkMode setting
    const stored = localStorage.getItem('darkMode');
    if (stored !== null) {
      return stored === 'true';
    }
    
    // Fall back to system preference
    if (window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    
    return false;
  });

  // Update document class and both storage locations when darkMode changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    // Write to both the old location and new settings format for backward compatibility
    localStorage.setItem('darkMode', darkMode.toString());
    
    // Update the new settings format if it exists
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        parsedSettings.appearance = { 
          ...parsedSettings.appearance,
          darkMode 
        };
        localStorage.setItem('appSettings', JSON.stringify(parsedSettings));
      }
    } catch (error) {
      console.error('Error updating appearance settings:', error);
    }
  }, [darkMode]);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setDarkMode(e.matches);
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Add keyboard shortcut listener
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'j') { // Ctrl+J to toggle dark mode
        setDarkMode((prev: boolean) => !prev);
      }
    };
    
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  return [darkMode, setDarkMode] as const;
}