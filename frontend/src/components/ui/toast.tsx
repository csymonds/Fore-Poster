import React from 'react';
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { Toast as ToastType, useToast } from '@/hooks/useToast';
import { cn } from '@/lib/utils';

interface ToastProps {
  toast: ToastType;
  onDismiss: () => void;
}

const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  // Map toast type to colors and icon
  const typeStyles = {
    success: {
      containerClass: 'bg-green-50 dark:bg-green-900 border-green-500 dark:border-green-700',
      textClass: 'text-green-800 dark:text-green-100',
      icon: <CheckCircle className="h-5 w-5 text-green-500 dark:text-green-400" />
    },
    error: {
      containerClass: 'bg-red-50 dark:bg-red-900 border-red-500 dark:border-red-700',
      textClass: 'text-red-800 dark:text-red-100',
      icon: <AlertCircle className="h-5 w-5 text-red-500 dark:text-red-400" />
    },
    warning: {
      containerClass: 'bg-yellow-50 dark:bg-yellow-900 border-yellow-500 dark:border-yellow-700',
      textClass: 'text-yellow-800 dark:text-yellow-100',
      icon: <AlertTriangle className="h-5 w-5 text-yellow-500 dark:text-yellow-400" />
    },
    info: {
      containerClass: 'bg-blue-50 dark:bg-blue-900 border-blue-500 dark:border-blue-700',
      textClass: 'text-blue-800 dark:text-blue-100',
      icon: <Info className="h-5 w-5 text-blue-500 dark:text-blue-400" />
    }
  };

  const style = typeStyles[toast.type] || typeStyles.info;

  return (
    <div 
      className={cn(
        'relative rounded-md border-l-4 p-4 shadow-md',
        style.containerClass,
        'animate-in slide-in-from-right fade-in duration-300'
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          {style.icon}
        </div>
        <div className="flex-1">
          <div className={cn('font-medium', style.textClass)}>
            {toast.title}
          </div>
          {toast.description && (
            <div className={cn('mt-1 text-sm', style.textClass)}>
              {toast.description}
            </div>
          )}
        </div>
        <button 
          onClick={onDismiss}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const { toasts, dismissToast } = useToast();

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {toasts.map(toast => (
        <Toast 
          key={toast.id} 
          toast={toast} 
          onDismiss={() => dismissToast(toast.id)} 
        />
      ))}
    </div>
  );
};

export default ToastContainer; 