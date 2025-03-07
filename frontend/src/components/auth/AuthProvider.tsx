// src/components/auth/AuthProvider.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { AuthApi } from '@/services/api';

interface User {
  token: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

const createSafeStorage = () => {
  let memoryStorage: { [key: string]: string } = {};
  
  const isLocalStorageAvailable = () => {
    try {
      localStorage.setItem('test', 'test');
      localStorage.removeItem('test');
      return true;
    } catch {
      return false;
    }
  };

  return {
    getItem: (key: string): string | null => {
      try {
        return isLocalStorageAvailable() 
          ? localStorage.getItem(key)
          : memoryStorage[key] || null;
      } catch {
        return memoryStorage[key] || null;
      }
    },
    setItem: (key: string, value: string): void => {
      try {
        if (isLocalStorageAvailable()) {
          localStorage.setItem(key, value);
        } else {
          memoryStorage[key] = value;
        }
      } catch {
        memoryStorage[key] = value;
      }
    },
    removeItem: (key: string): void => {
      try {
        if (isLocalStorageAvailable()) {
          localStorage.removeItem(key);
        } else {
          delete memoryStorage[key];
        }
      } catch {
        delete memoryStorage[key];
      }
    }
  };
};

const safeStorage = createSafeStorage();

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const token = safeStorage.getItem('token');
    return token ? { token } : null;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      const token = safeStorage.getItem('token');
      console.log('Initial token:', token ? 'Present' : 'Not found');
      
      if (token) {
        console.log('Validating token...');
        const isValid = await validateToken(token);
        console.log('Token validation result:', isValid);

        if (isValid) {
          setUser({ token });
        } else {
          console.log('Removing invalid token');
          safeStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const validateToken = async (token: string): Promise<boolean> => {
    try {
      console.log('Making validation request...');
      const isValid = await AuthApi.validateToken(token);
      console.log('Validation response:', isValid);
      return isValid;
    } catch (err) {
      console.error('Token validation error:', err);
      setError('Session expired. Please login again.');
      return false;
    }
  };

  const login = async (username: string, password: string): Promise<void> => {
    try {
      console.log('Attempting login...');
      const token = await AuthApi.login(username, password);
      console.log('Login successful, token received:', token ? 'Present' : 'Missing');
      
      if (!token) {
        throw new Error('No token received from server');
      }
      
      safeStorage.setItem('token', token);
      setUser({ token });
      setError(null);
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    }
  };

  const logout = () => {
    safeStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, error }}>
      {children}
    </AuthContext.Provider>
  );
};

export const LoginForm = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const auth = useContext(AuthContext);

  if (!auth) throw new Error('useAuth must be used within AuthProvider');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await auth.login(formData.username, formData.password);
    } catch (err) {
      console.error('Login submission error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-sm mx-4">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Login to Fore-Poster
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form id="fore-poster-login" onSubmit={handleSubmit} className="space-y-4">
            {auth.error && (
              <Alert variant="destructive">
                <AlertDescription>{auth.error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                value={formData.username}
                onChange={handleChange}
                disabled={isLoading}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="current-password">Password</Label>
              <Input
                id="current-password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                disabled={isLoading}
                required
              />
            </div>
          </form>
        </CardContent>
        <CardFooter>
          <Button 
            form="fore-poster-login"
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Signing in...
              </span>
            ) : (
              'Sign in'
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  
  if (!user) {
    return <LoginForm />;
  }
  
  return <>{children}</>;
};