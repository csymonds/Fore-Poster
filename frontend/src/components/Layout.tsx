import React, { useState } from 'react';
import { Settings, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from './auth/AuthProvider';
import SettingsModal from './SettingsModal';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { logout } = useAuth();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <nav className="bg-card border-b-2 border-indigo-400 dark:border-indigo-500 shadow-sm">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-foreground">Fore-Poster</span>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={() => setIsSettingsOpen(true)}
                className="border-2 border-indigo-400 dark:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-950 flex items-center gap-2"
              >
                <Settings className="h-5 w-5" />
                Settings
              </Button>
              <Button
                variant="outline"
                onClick={logout}
                className="border-2 border-rose-400 dark:border-rose-500 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950 flex items-center gap-2"
              >
                <LogOut className="h-5 w-5" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {children}

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
};

export default Layout;