import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface SSEOptions {
  url?: string;
  onMessage?: (event: MessageEvent) => void;
  onError?: (error: Event) => void;
}

/**
 * Hook to connect to Server-Sent Events for real-time updates
 */
export const useSSE = (options: SSEOptions = {}) => {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Get API base URL from environment for default URL
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
  const baseUrl = apiBaseUrl.endsWith('/api') ? apiBaseUrl : `${apiBaseUrl}/api`;
  const defaultUrl = `${baseUrl}/events`;

  // Use provided URL or default
  const url = options.url || defaultUrl;
  const { onMessage, onError } = options;

  useEffect(() => {
    console.log(`🔄 Setting up SSE connection to ${url}`);
    
    // Force immediate return in development if SSE disabled
    const enableSSE = import.meta.env.VITE_ENABLE_SSE === 'true';
    if (import.meta.env.DEV && !enableSSE) {
      console.log('⚠️ SSE explicitly disabled in development. Set VITE_ENABLE_SSE=true to enable.');
      return;
    }

    // Check if EventSource is supported in this browser
    if (!window.EventSource) {
      console.error('⛔ EventSource is not supported in this browser');
      setError('EventSource not supported in this browser');
      return;
    }

    let eventSource: EventSource | null = null;
    try {
      // Create a new event source
      console.log(`📡 Creating EventSource for ${url}`);
      eventSource = new EventSource(url);
      
      // Handle connection open
      eventSource.onopen = () => {
        console.log('✅ SSE connection established');
        setConnected(true);
        setError(null);
      };

      // Handle all messages
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 SSE message received:', data);
          
          // Handle different event types from the existing backend
          if (data.type === 'connected') {
            console.log('🔗 SSE connection confirmed by server');
          } else if (data.type === 'heartbeat') {
            console.log('💓 SSE heartbeat received');
          } else if (data.type === 'post_update') {
            console.log('📝 Post update received:', data.data);
            // Invalidate posts query to trigger a refetch
            queryClient.invalidateQueries({ queryKey: ['posts'] });
            
            // Call custom handler if provided
            if (onMessage) {
              onMessage(event);
            }
          }
        } catch (e) {
          console.error('❌ Error parsing SSE message:', e);
        }
      };

      // Handle errors
      eventSource.onerror = (e) => {
        console.error('❌ SSE connection error:', e);
        setConnected(false);
        setError('Connection error');
        
        if (onError) {
          onError(e);
        }
        
        // Try to close the connection on error
        try {
          eventSource?.close();
        } catch (closeError) {
          console.error('Error closing SSE connection after error:', closeError);
        }
      };

      // Clean up the connection when component unmounts
      return () => {
        console.log('🔒 Closing SSE connection');
        eventSource?.close();
        setConnected(false);
      };
    } catch (e) {
      console.error('⛔ Error setting up SSE:', e);
      setError(`Setup error: ${e instanceof Error ? e.message : String(e)}`);
      setConnected(false);
      
      // Try to close the connection on error
      try {
        eventSource?.close();
      } catch (closeError) {
        console.error('Error closing SSE connection after setup error:', closeError);
      }
    }
  }, [url, queryClient, onMessage, onError]);

  // Return both connected and isConnected for backward compatibility
  return { connected, isConnected: connected, error };
};

export default useSSE; 