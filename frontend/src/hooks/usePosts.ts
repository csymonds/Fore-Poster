// src/hooks/usePosts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PostsApi, CreatePostPayload, UpdatePostPayload } from '@/services/api';
import { useSSE } from './useSSE';
import { useEffect } from 'react';

// Only use polling as a fallback if SSE isn't available 
// Default interval in milliseconds (30 seconds instead of 5)
const DEFAULT_REFETCH_INTERVAL = 30000;

export const usePosts = (options = {}) => {
  // Get API base URL from environment
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
  const baseUrl = apiBaseUrl.endsWith('/api') ? apiBaseUrl : `${apiBaseUrl}/api`;
  const sseUrl = `${baseUrl}/events`;
  
  // Set up SSE connection for real-time updates
  const { connected: sseConnected } = useSSE({
    url: sseUrl
  });
  
  const query = useQuery({
    queryKey: ['posts'],
    queryFn: () => PostsApi.getPosts(),
    // Only use polling as a fallback if SSE isn't connected
    refetchInterval: sseConnected ? false : DEFAULT_REFETCH_INTERVAL,
    // Always refetch when window regains focus
    refetchOnWindowFocus: true,
    ...options
  });

  // Log SSE connection status
  useEffect(() => {
    if (sseConnected) {
      console.log('Using SSE for real-time post updates');
    } else {
      console.log('SSE not connected, falling back to polling');
    }
  }, [sseConnected]);
  
  return query;
};

export const useCreatePost = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (post: CreatePostPayload) => PostsApi.createPost(post),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });
};

export const useUpdatePost = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, post }: { id: number; post: UpdatePostPayload }) => 
      PostsApi.updatePost(id, post),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });
};

export const useDeletePost = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => PostsApi.deletePost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });
};

export const usePostNow = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => PostsApi.postNow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });
};