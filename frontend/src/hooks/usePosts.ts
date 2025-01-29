// src/hooks/usePosts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PostsApi, CreatePostPayload, UpdatePostPayload } from '@/services/api';

export const usePosts = () => {
  return useQuery({
    queryKey: ['posts'],
    queryFn: () => PostsApi.getPosts()
  });
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