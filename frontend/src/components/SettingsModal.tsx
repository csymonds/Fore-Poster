import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, SunIcon, Clock3Icon, MoonIcon } from 'lucide-react';
import { useDarkMode } from '@/hooks/useDarkMode';
import { useSettings, TimePreference } from '@/hooks/useSettings';
import { SettingsApi } from '@/services/api';
import { useToast } from '@/hooks/useToast';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Helper component for time input fields
const TimeInput: React.FC<{
  label: string;
  icon: React.ReactNode;
  value: TimePreference;
  onChange: (newValue: TimePreference) => void;
}> = ({ label, icon, value, onChange }) => {
  const handleHourChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const hour = parseInt(e.target.value);
    if (hour >= 0 && hour <= 23) {
      onChange({ ...value, hour });
    }
  };

  const handleMinuteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const minute = parseInt(e.target.value);
    if (minute >= 0 && minute <= 59) {
      onChange({ ...value, minute });
    }
  };

  return (
    <div className="flex items-center space-x-3">
      <div className="flex-shrink-0">
        {icon}
      </div>
      <Label className="flex-grow">{label}</Label>
      <div className="flex items-center space-x-1">
        <Input
          type="number"
          min={0}
          max={23}
          value={value.hour}
          onChange={handleHourChange}
          className="w-16"
        />
        <span>:</span>
        <Input
          type="number"
          min={0}
          max={59}
          value={value.minute}
          onChange={handleMinuteChange}
          className="w-16"
        />
      </div>
    </div>
  );
};

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [darkMode, setDarkMode] = useDarkMode();
  const { settings, updatePreferences, updateAI, updatePosts, resetSettings } = useSettings();
  const { toast } = useToast();
  const [isSyncing, setIsSyncing] = useState(false);
  const [activeTab, setActiveTab] = useState('preferences');

  // Track if we've modified settings that require backend sync
  const [aiSettingsModified, setAiSettingsModified] = useState(false);

  // Local state for editing
  const [localPreferences, setLocalPreferences] = useState({
    darkMode: settings.preferences.darkMode,
    optimalTimes: [...settings.preferences.optimalTimes]
  });

  const [localAISettings, setLocalAISettings] = useState({
    systemPrompt: settings.ai.systemPrompt,
    temperature: settings.ai.temperature,
    shouldUseWebSearch: settings.ai.shouldUseWebSearch
  });
  
  const [localPostSettings, setLocalPostSettings] = useState({
    autoArchiveDays: settings.posts.autoArchiveDays,
    defaultPlatform: settings.posts.defaultPlatform
  });

  // Update local state when settings change
  useEffect(() => {
    setLocalPreferences({
      darkMode: settings.preferences.darkMode,
      optimalTimes: [...settings.preferences.optimalTimes]
    });

    setLocalAISettings({
      systemPrompt: settings.ai.systemPrompt,
      temperature: settings.ai.temperature,
      shouldUseWebSearch: settings.ai.shouldUseWebSearch
    });
    
    setLocalPostSettings({
      autoArchiveDays: settings.posts.autoArchiveDays,
      defaultPlatform: settings.posts.defaultPlatform
    });
  }, [settings]);

  // Update dark mode when the dark mode setting changes
  useEffect(() => {
    setLocalPreferences(prev => ({
      ...prev,
      darkMode
    }));
  }, [darkMode]);

  // Sync AI settings with backend
  const syncAISettings = async () => {
    setIsSyncing(true);
    try {
      // Log the data we're sending to the server
      console.log('Syncing AI settings:', {
        systemPrompt: localAISettings.systemPrompt,
        temperature: localAISettings.temperature,
        webSearchEnabled: localAISettings.shouldUseWebSearch
      });
      
      await SettingsApi.syncAISettings({
        systemPrompt: localAISettings.systemPrompt,
        temperature: localAISettings.temperature,
        webSearchEnabled: localAISettings.shouldUseWebSearch
      });
      
      // Update local settings
      updateAI(localAISettings);
      
      toast({
        title: "Settings saved",
        description: "AI settings have been synchronized with the server.",
        type: "success"
      });
      
      setAiSettingsModified(false);
    } catch (error) {
      console.error('Failed to sync AI settings:', error);
      let errorMessage = 'Failed to synchronize AI settings with the server.';
      
      // Try to extract more detailed error information
      if (error instanceof Error) {
        errorMessage += ` Error: ${error.message}`;
      }
      
      toast({
        title: "Error saving settings",
        description: errorMessage,
        type: "error"
      });
    } finally {
      setIsSyncing(false);
    }
  };

  // Handle time setting changes
  const handleTimeChange = (index: number, newValue: TimePreference) => {
    const updatedTimes = [...localPreferences.optimalTimes];
    updatedTimes[index] = { ...newValue };
    setLocalPreferences(prev => ({
      ...prev,
      optimalTimes: updatedTimes
    }));
  };

  // Save all local changes to settings store
  const saveSettings = () => {
    // Update Preferences
    updatePreferences(localPreferences);
    
    // Update AI settings
    updateAI(localAISettings);
    
    // Update post management settings
    updatePosts(localPostSettings);
    
    // Set dark mode (which will also update localStorage)
    if (darkMode !== localPreferences.darkMode) {
      setDarkMode(localPreferences.darkMode);
    }
    
    // Sync with backend if needed
    if (aiSettingsModified) {
      syncAISettings();
    } else {
      toast({
        title: "Settings saved",
        description: "Your settings have been updated.",
        type: "success"
      });
    }
    
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Customize your Fore-Poster experience
          </DialogDescription>
        </DialogHeader>
        
        <Tabs defaultValue="preferences" value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-3 mb-4">
            <TabsTrigger value="preferences">Preferences</TabsTrigger>
            <TabsTrigger value="ai">AI Settings</TabsTrigger>
            <TabsTrigger value="posts">Post Management</TabsTrigger>
          </TabsList>
          
          {/* Preferences Tab (formerly Appearance) */}
          <TabsContent value="preferences" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Theme</CardTitle>
                <CardDescription>Customize the application appearance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="dark-mode" className="flex flex-col space-y-1">
                    <span>Dark Mode</span>
                    <span className="text-sm text-muted-foreground">
                      Toggle dark mode (Ctrl+J)
                    </span>
                  </Label>
                  <Switch
                    id="dark-mode"
                    checked={localPreferences.darkMode}
                    onCheckedChange={(checked) => 
                      setLocalPreferences(prev => ({ ...prev, darkMode: checked }))
                    }
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Optimal Post Times</CardTitle>
                <CardDescription>Customize when your posts are scheduled</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground mb-2">
                  Set your preferred posting times for the quick scheduling buttons
                </p>
                
                <TimeInput 
                  label="Morning"
                  icon={<SunIcon className="h-5 w-5 text-indigo-500" />}
                  value={localPreferences.optimalTimes[0]}
                  onChange={(newValue) => handleTimeChange(0, newValue)}
                />
                
                <TimeInput 
                  label="Noon"
                  icon={<Clock3Icon className="h-5 w-5 text-indigo-500" />}
                  value={localPreferences.optimalTimes[1]}
                  onChange={(newValue) => handleTimeChange(1, newValue)}
                />
                
                <TimeInput 
                  label="Evening"
                  icon={<MoonIcon className="h-5 w-5 text-indigo-500" />}
                  value={localPreferences.optimalTimes[2]}
                  onChange={(newValue) => handleTimeChange(2, newValue)}
                />
                
                <p className="text-xs text-muted-foreground mt-2">
                  Times are displayed in 24-hour format. Example: 18:00 is 6:00 PM.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* AI Settings Tab */}
          <TabsContent value="ai" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>AI Configuration</CardTitle>
                <CardDescription>Customize how the AI generates content</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="system-prompt">System Prompt</Label>
                  <Textarea
                    id="system-prompt"
                    value={localAISettings.systemPrompt}
                    onChange={(e) => {
                      setLocalAISettings(prev => ({...prev, systemPrompt: e.target.value}));
                      setAiSettingsModified(true);
                    }}
                    rows={4}
                    placeholder="Enter system instructions for the AI"
                    className="resize-none"
                  />
                  <p className="text-xs text-muted-foreground">
                    These instructions define how the AI responds when generating post content
                  </p>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <Label htmlFor="temperature">Temperature: {localAISettings.temperature.toFixed(1)}</Label>
                  </div>
                  <Slider
                    id="temperature"
                    min={0}
                    max={2}
                    step={0.1}
                    value={[localAISettings.temperature]}
                    onValueChange={(values: number[]) => {
                      setLocalAISettings(prev => ({...prev, temperature: values[0]}));
                      setAiSettingsModified(true);
                    }}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Predictable (0.0)</span>
                    <span>Creative (2.0)</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between pt-2">
                  <Label htmlFor="web-search" className="flex flex-col space-y-1">
                    <span>Enable Web Search</span>
                    <span className="text-sm text-muted-foreground">
                      Allow AI to search the web for current information
                    </span>
                  </Label>
                  <Switch
                    id="web-search"
                    checked={localAISettings.shouldUseWebSearch}
                    onCheckedChange={(checked) => {
                      setLocalAISettings(prev => ({...prev, shouldUseWebSearch: checked}));
                      setAiSettingsModified(true);
                    }}
                  />
                </div>
                
                {aiSettingsModified && (
                  <div className="flex items-start gap-2 mt-4 p-2 bg-yellow-100 dark:bg-yellow-900 rounded-md text-sm">
                    <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <p className="text-yellow-800 dark:text-yellow-200">
                      AI settings changes need to be synchronized with the server to take effect.
                    </p>
                  </div>
                )}
              </CardContent>
              <CardFooter className="justify-end">
                <Button 
                  onClick={syncAISettings} 
                  disabled={!aiSettingsModified || isSyncing}
                  variant="outline"
                >
                  {isSyncing ? "Syncing..." : "Sync with Server"}
                </Button>
              </CardFooter>
            </Card>
          </TabsContent>
          
          {/* Post Management Tab */}
          <TabsContent value="posts" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Post Management</CardTitle>
                <CardDescription>Configure how posts are managed</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="archive-days">Auto-archive posts after (days)</Label>
                  <Input
                    id="archive-days"
                    type="number"
                    min={1}
                    max={365}
                    value={localPostSettings.autoArchiveDays}
                    onChange={(e) => setLocalPostSettings(prev => ({
                      ...prev, 
                      autoArchiveDays: parseInt(e.target.value) || 30
                    }))}
                  />
                  <p className="text-xs text-muted-foreground">
                    Posts older than this will be automatically archived
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="default-platform">Default Platform</Label>
                  <select
                    id="default-platform"
                    value={localPostSettings.defaultPlatform}
                    onChange={(e) => setLocalPostSettings(prev => ({
                      ...prev, 
                      defaultPlatform: e.target.value
                    }))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  >
                    <option value="x">X (Twitter)</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="facebook">Facebook</option>
                  </select>
                </div>
                
                <div className="pt-4">
                  <Button variant="destructive" onClick={() => {
                    const confirmed = window.confirm("This will permanently delete all posted and failed posts that are older than 30 days. Continue?");
                    if (confirmed) {
                      toast({
                        title: "Cleanup initiated",
                        description: "Old posts are being deleted. This may take a moment.",
                        type: "info"
                      });
                    }
                  }}>
                    Clean Up Old Posts
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        
        <div className="flex justify-between mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <div className="space-x-2">
            <Button variant="outline" onClick={resetSettings}>
              Reset All
            </Button>
            <Button onClick={saveSettings}>
              Save Changes
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SettingsModal;