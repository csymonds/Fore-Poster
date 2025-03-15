import { useEffect, useState } from 'react';

export function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    console.log("Initializing dark mode from storage");
    
    // Check for settings in the preferences structure
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        // Only check preferences (new location)
        if (parsedSettings.preferences && 'darkMode' in parsedSettings.preferences) {
          console.log(`Found dark mode in preferences: ${parsedSettings.preferences.darkMode}`);
          return parsedSettings.preferences.darkMode;
        }
      }
    } catch (error) {
      console.error('Error reading settings format:', error);
    }
    
    // Fall back to system preference if no settings found
    if (window.matchMedia) {
      const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
      console.log(`Using system preference for dark mode: ${systemPreference}`);
      return systemPreference;
    }
    
    console.log("No dark mode preference found, defaulting to false");
    return false;
  });

  // Update document class and store settings when darkMode changes
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
        // Create default settings object if none exists
        let parsedSettings;
        const storedSettings = localStorage.getItem('appSettings');
        
        if (storedSettings) {
          parsedSettings = JSON.parse(storedSettings);
        } else {
          console.log("Creating new appSettings object");
          parsedSettings = { preferences: {} };
        }
        
        // Ensure preferences exists
        if (!parsedSettings.preferences) {
          parsedSettings.preferences = {};
        }
        
        // Update the preferences settings - only use the new structure
        parsedSettings.preferences.darkMode = darkMode;
        
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
        console.error('Error updating preferences settings:', error);
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