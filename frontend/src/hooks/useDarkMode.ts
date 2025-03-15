import { useEffect, useState } from 'react';

export function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    console.log("Initializing dark mode from storage");
    
    // Check for the newer settings format first
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        if (parsedSettings.appearance && 'darkMode' in parsedSettings.appearance) {
          console.log(`Found dark mode in appSettings: ${parsedSettings.appearance.darkMode}`);
          return parsedSettings.appearance.darkMode;
        }
      }
    } catch (error) {
      console.error('Error reading newer settings format:', error);
    }
    
    // Fall back to the old standalone darkMode setting
    const stored = localStorage.getItem('darkMode');
    if (stored !== null) {
      console.log(`Found dark mode in legacy storage: ${stored}`);
      return stored === 'true';
    }
    
    // Fall back to system preference
    if (window.matchMedia) {
      const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
      console.log(`Using system preference for dark mode: ${systemPreference}`);
      return systemPreference;
    }
    
    console.log("No dark mode preference found, defaulting to false");
    return false;
  });

  // Update document class and both storage locations when darkMode changes
  useEffect(() => {
    console.log(`Dark mode changed to: ${darkMode}`);
    
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    // Create a function to save settings
    const saveSettings = () => {
      try {
        // Write to both the old location and new settings format for backward compatibility
        console.log(`Saving dark mode (${darkMode}) to localStorage`);
        localStorage.setItem('darkMode', darkMode.toString());
        
        // Create default settings object if none exists
        let parsedSettings;
        const storedSettings = localStorage.getItem('appSettings');
        
        if (storedSettings) {
          parsedSettings = JSON.parse(storedSettings);
        } else {
          console.log("Creating new appSettings object");
          parsedSettings = { appearance: {} };
        }
        
        // Update the appearance settings
        parsedSettings.appearance = { 
          ...parsedSettings.appearance,
          darkMode 
        };
        
        // Save the updated settings
        const settingsJson = JSON.stringify(parsedSettings);
        localStorage.setItem('appSettings', settingsJson);
        console.log(`Saved appSettings: ${settingsJson}`);
        
        // Verify the save was successful
        const verification = localStorage.getItem('appSettings');
        if (verification !== settingsJson) {
          console.error("Storage verification failed");
        }
      } catch (error) {
        console.error('Error updating appearance settings:', error);
      }
    };
    
    // Call the save function
    saveSettings();
    
    // Also save when the window is about to unload
    const handleBeforeUnload = () => {
      saveSettings();
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [darkMode]);

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      console.log(`System dark mode preference changed to: ${e.matches}`);
      setDarkMode(e.matches);
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Add keyboard shortcut listener
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'j') { // Ctrl+J to toggle dark mode
        console.log('Dark mode keyboard shortcut detected');
        setDarkMode((prev: boolean) => !prev);
      }
    };
    
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  return [darkMode, setDarkMode] as const;
}