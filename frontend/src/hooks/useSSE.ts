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
 * @returns Object with connection status
 */
export const useSSE = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    // Connect to the SSE endpoint
    const apiUrl = import.meta.env.VITE_API_URL || '';
    const url = `${apiUrl}/api/events`;
    
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;
    
    // Set up event handlers
    eventSource.onopen = () => {
      console.log('SSE connection opened');
      setIsConnected(true);
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      setIsConnected(false);
      
      // Try to reconnect after a delay
      setTimeout(() => {
        eventSource.close();
        const newEventSource = new EventSource(url);
        eventSourceRef.current = newEventSource;
        // Re-assign event handlers
        newEventSource.onopen = eventSource.onopen;
        newEventSource.onerror = eventSource.onerror;
        newEventSource.onmessage = eventSource.onmessage;
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
  }, [queryClient]);
  
  return { isConnected, lastEvent };
};

export default useSSE; 