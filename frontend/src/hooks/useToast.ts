import { useState, useCallback, useEffect } from 'react';

// Toast types for different statuses
export type ToastType = 'success' | 'error' | 'warning' | 'info';

// Toast interface
export interface Toast {
  id: string;
  title: string;
  description?: string;
  type: ToastType;
  duration?: number;
}

// Toast options for creating new toasts
export interface ToastOptions {
  title: string;
  description?: string;
  type?: ToastType;
  duration?: number;
}

// Generated ID for toasts
const generateId = (): string => {
  return Math.random().toString(36).substring(2, 9);
};

// Singleton toast store for managing toasts across components
interface ToastStore {
  toasts: Toast[];
  listeners: Array<(toasts: Toast[]) => void>;
  subscribe: (listener: (toasts: Toast[]) => void) => () => void;
  addToast: (options: ToastOptions) => string;
  removeToast: (id: string) => void;
}

const toastStore: ToastStore = {
  toasts: [],
  listeners: [],
  
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  },
  
  addToast(options) {
    const { title, description, type = 'info', duration = 5000 } = options;
    const id = generateId();
    
    const newToast: Toast = {
      id,
      title,
      description,
      type,
      duration
    };
    
    this.toasts = [...this.toasts, newToast];
    this.listeners.forEach(listener => listener(this.toasts));
    
    // Auto-dismiss
    if (duration) {
      setTimeout(() => {
        this.removeToast(id);
      }, duration);
    }
    
    return id;
  },
  
  removeToast(id) {
    this.toasts = this.toasts.filter(toast => toast.id !== id);
    this.listeners.forEach(listener => listener(this.toasts));
  }
};

// React hook for consuming the toast store
export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>(toastStore.toasts);
  
  useEffect(() => {
    return toastStore.subscribe(setToasts);
  }, []);
  
  const toast = useCallback((options: ToastOptions) => {
    return toastStore.addToast(options);
  }, []);
  
  const dismissToast = useCallback((id: string) => {
    toastStore.removeToast(id);
  }, []);
  
  return {
    toasts,
    toast,
    dismissToast
  };
} 