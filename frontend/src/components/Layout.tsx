import React from 'react';
import { Settings, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from './auth/AuthProvider';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-100">
      <nav className="bg-white shadow-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-slate-900">Fore-Poster</span>
            </div>
            <div className="flex items-center space-x-4">
              <Button 
                variant="ghost" 
                className="bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium py-2 px-4 rounded-lg flex items-center gap-2"
              >
                <Settings className="h-5 w-5" />
                Settings
              </Button>
              <Button 
                variant="ghost" 
                onClick={logout}
                className="bg-rose-50 hover:bg-rose-100 text-rose-700 font-medium py-2 px-4 rounded-lg flex items-center gap-2"
              >
                <LogOut className="h-5 w-5" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>
      
      {children}
    </div>
  );
};

export default Layout;