import { useState, useEffect, useCallback } from 'react';
import { DEFAULT_OPTIMAL_POSTING_TIMES } from '@/utils/dateUtils';

// Define time settings for morning, noon, evening
export interface TimePreference {
  hour: number;
  minute: number;
  name: string;
}

// Preferences includes both appearance and time settings
export interface PreferencesSettings {
  darkMode: boolean;
  optimalTimes: TimePreference[];
}

export interface AISettings {
  systemPrompt: string;
  temperature: number;
  shouldUseWebSearch: boolean;
}

export interface PostSettings {
  autoArchiveDays: number;
  defaultPlatform: string;
}

// Combine all settings into one type
export interface Settings {
  preferences: PreferencesSettings;
  ai: AISettings;
  posts: PostSettings;
}

// Default settings values
const DEFAULT_SETTINGS: Settings = {
  preferences: {
    darkMode: false, // Will be overridden by useDarkMode
    optimalTimes: DEFAULT_OPTIMAL_POSTING_TIMES,
  },
  ai: {
    systemPrompt: "You are a social media expert who writes engaging, factual posts for X (formerly Twitter). Your goal is growing your audience and get attention. Make the algorithm happy. Keep it under 280 characters. Avoid exclamation marks. Don't be cringe. Don't be cheesy. Use emojis",
    temperature: 0.7,
    shouldUseWebSearch: true,
  },
  posts: {
    autoArchiveDays: 30,
    defaultPlatform: 'x',
  },
};

// Type for update functions
type UpdateSettings<T> = (settings: Partial<T>) => void;

// Main hook
export function useSettings() {
  // Initialize state with values from localStorage or defaults
  const [settings, setSettings] = useState<Settings>(() => {
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        // Parse stored settings and merge with defaults for any new settings
        const parsedSettings = JSON.parse(storedSettings);
        
        return {
          preferences: { 
            ...DEFAULT_SETTINGS.preferences, 
            ...parsedSettings.preferences,
          },
          ai: { ...DEFAULT_SETTINGS.ai, ...parsedSettings.ai },
          posts: { ...DEFAULT_SETTINGS.posts, ...parsedSettings.posts },
        };
      }
    } catch (error) {
      console.error('Error loading settings from localStorage:', error);
    }
    return DEFAULT_SETTINGS;
  });

  // Save to localStorage whenever settings change
  useEffect(() => {
    try {
      localStorage.setItem('appSettings', JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving settings to localStorage:', error);
    }
  }, [settings]);

  // Update functions for each settings category
  const updatePreferences = useCallback<UpdateSettings<PreferencesSettings>>((newSettings) => {
    setSettings(prev => ({
      ...prev,
      preferences: { ...prev.preferences, ...newSettings },
    }));
  }, []);

  const updateAI = useCallback<UpdateSettings<AISettings>>((newSettings) => {
    setSettings(prev => ({
      ...prev,
      ai: { ...prev.ai, ...newSettings },
    }));
  }, []);

  const updatePosts = useCallback<UpdateSettings<PostSettings>>((newSettings) => {
    setSettings(prev => ({
      ...prev,
      posts: { ...prev.posts, ...newSettings },
    }));
  }, []);

  // Reset all settings to defaults
  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  return {
    settings,
    updatePreferences,
    updateAI,
    updatePosts,
    resetSettings,
  };
}

// Export a singleton instance for use throughout the app
export const settingsStore = {
  getSystemPrompt: (): string => {
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        return parsedSettings.ai?.systemPrompt || DEFAULT_SETTINGS.ai.systemPrompt;
      }
    } catch (error) {
      console.error('Error loading system prompt from localStorage:', error);
    }
    return DEFAULT_SETTINGS.ai.systemPrompt;
  },
  
  getTemperature: (): number => {
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        return parsedSettings.ai?.temperature || DEFAULT_SETTINGS.ai.temperature;
      }
    } catch (error) {
      console.error('Error loading temperature from localStorage:', error);
    }
    return DEFAULT_SETTINGS.ai.temperature;
  },
  
  shouldUseWebSearch: (): boolean => {
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        return parsedSettings.ai?.shouldUseWebSearch ?? DEFAULT_SETTINGS.ai.shouldUseWebSearch;
      }
    } catch (error) {
      console.error('Error loading web search setting from localStorage:', error);
    }
    return DEFAULT_SETTINGS.ai.shouldUseWebSearch;
  },
  
  getOptimalTimes: (): TimePreference[] => {
    try {
      const storedSettings = localStorage.getItem('appSettings');
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings);
        return parsedSettings.preferences?.optimalTimes || DEFAULT_SETTINGS.preferences.optimalTimes;
      }
    } catch (error) {
      console.error('Error loading optimal times from localStorage:', error);
    }
    return DEFAULT_SETTINGS.preferences.optimalTimes;
  }
}; 