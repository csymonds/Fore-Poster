import { useState, useEffect, useRef } from 'react';
import { Post } from '@/services/api';
import { useQueryClient } from '@tanstack/react-query';

// Define the types of events we expect from the server
interface SSEEvent {
  type: 'connected' | 'heartbeat' | 'post_update';
  data?: Post;
}

/**
 * Hook to subscribe to Server-Sent Events for real-time updates
 * 
 * @returns Object with connection status and error information
 */
export const useSSE = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();
  
  // Maximum number of retry attempts
  const MAX_RETRIES = 3;

  useEffect(() => {
    // Only attempt to connect if we haven't exceeded the retry limit
    if (retryCount > MAX_RETRIES) {
      setConnectionError('Maximum retry attempts reached. Live updates are disabled.');
      return;
    }

    // Connect to the SSE endpoint using the correct environment variable
    // Remove the '/api' part from the end since we'll add it ourselves
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
    const baseUrl = apiBaseUrl.endsWith('/api') ? apiBaseUrl : `${apiBaseUrl}/api`;
    const url = `${baseUrl}/events`;
    
    console.log(`Connecting to SSE endpoint: ${url} (Attempt ${retryCount + 1}/${MAX_RETRIES + 1})`);
    
    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;
      
      // Set up event handlers
      eventSource.onopen = () => {
        console.log('SSE connection opened');
        setIsConnected(true);
        setConnectionError(null);
        // Reset retry count on successful connection
        setRetryCount(0);
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        setIsConnected(false);
        
        // Increment retry count
        setRetryCount(prev => prev + 1);
        
        // If we've exceeded the retry limit, stop trying
        if (retryCount >= MAX_RETRIES) {
          setConnectionError('Failed to establish connection to the server. Live updates are disabled.');
          console.warn('SSE connection failed after maximum retries');
          eventSource.close();
          return;
        }
        
        // Try to reconnect after a delay
        setTimeout(() => {
          console.log(`Reconnecting to SSE endpoint: ${url} (Attempt ${retryCount + 2}/${MAX_RETRIES + 1})`);
          eventSource.close();
          
          // The next connection attempt will happen when the component re-renders
          // due to the retryCount state change
        }, 5000);
      };
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as SSEEvent;
          setLastEvent(data);
          
          // Handle different event types
          switch (data.type) {
            case 'connected':
              console.log('SSE connection established');
              setIsConnected(true);
              setConnectionError(null);
              break;
              
            case 'heartbeat':
              // Keep-alive message, no action needed
              break;
              
            case 'post_update':
              if (data.data) {
                console.log('Received post update:', data.data);
                // Update the React Query cache with the new data
                queryClient.setQueryData<Post[] | undefined>(
                  ['posts'],
                  (oldPosts) => {
                    if (!oldPosts) return undefined;
                    
                    // Find and update the post in the cache
                    return oldPosts.map(post => 
                      post.id === data.data?.id ? data.data : post
                    );
                  }
                );
              }
              break;
          }
        } catch (error) {
          console.error('Error parsing SSE message:', error);
        }
      };
      
      // Clean up on unmount
      return () => {
        eventSource.close();
      };
    } catch (error) {
      console.error('Error creating EventSource:', error);
      setConnectionError('Failed to establish connection to the server. Live updates are disabled.');
    }
  }, [queryClient, retryCount]);
  
  return { 
    isConnected, 
    lastEvent,
    connectionError,
    hasExceededRetries: retryCount > MAX_RETRIES
  };
};

export default useSSE; 