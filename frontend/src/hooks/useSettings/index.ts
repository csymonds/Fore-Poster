import { useState, useEffect, useCallback } from 'react';

// Define types for different settings categories
export interface AppearanceSettings {
  darkMode: boolean;
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
  appearance: AppearanceSettings;
  ai: AISettings;
  posts: PostSettings;
}

// Default settings values
const DEFAULT_SETTINGS: Settings = {
  appearance: {
    darkMode: false, // Will be overridden by useDarkMode
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
        // Merge stored settings with defaults for any new settings
        const parsedSettings = JSON.parse(storedSettings);
        return {
          appearance: { ...DEFAULT_SETTINGS.appearance, ...parsedSettings.appearance },
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
  const updateAppearance = useCallback<UpdateSettings<AppearanceSettings>>((newSettings) => {
    setSettings(prev => ({
      ...prev,
      appearance: { ...prev.appearance, ...newSettings },
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
    updateAppearance,
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
  }
}; 