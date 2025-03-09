// src/services/api.ts

// Vite environment type declaration
/// <reference types="vite/client" />

export interface Post {
  id: number;
  content: string;
  scheduled_time: string;
  status: 'draft' | 'scheduled' | 'posted' | 'failed';
  platform: string;
  post_id?: string;
  image_url?: string | null;
  image_filename?: string | null;
}

export interface CreatePostPayload {
  content: string;
  scheduled_time: string;
  platform: string;
  status: Post['status']; // Required, will always be set to 'draft' by default
  image_url?: string | null;
  image_filename?: string | null;
}

export interface UpdatePostPayload {
  content?: string;
  scheduled_time?: string;
  platform?: string;
  status?: Post['status'];
  image_url?: string | null;
  image_filename?: string | null;
}

export interface ImageUploadResponse {
  filename: string;
  url: string;
  original_filename: string;
}

interface ApiError {
  error: string;
  status?: number;
  details?: any;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Helper function to consistently build API URLs
 */
const getFullUrl = (endpoint: string): string => {
  // Remove any trailing slash from base URL
  const baseUrl = API_BASE_URL.endsWith('/') 
    ? API_BASE_URL.slice(0, -1) 
    : API_BASE_URL;
  
  // Ensure endpoint starts with a slash
  const formattedEndpoint = endpoint.startsWith('/') 
    ? endpoint 
    : `/${endpoint}`;
  
  return `${baseUrl}${formattedEndpoint}`;
};

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};

const handleApiError = async (response: Response): Promise<never> => {
  let error: ApiError;
  try {
    error = await response.json();
  } catch {
    error = {
      error: `HTTP error ${response.status}`,
      status: response.status,
    };
  }
  throw new Error(error.error || `HTTP error ${response.status}`);
};

export class AuthApi {
  static async login(username: string, password: string): Promise<string> {
    const url = getFullUrl('login');
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      
      if (!response.ok) {
        return handleApiError(response);
      }

      const data = await response.json();
      return data.token;
    } catch (error) {
      console.error('Network error during login:', error);
      throw error;
    }
  }

  static async validateToken(token: string): Promise<boolean> {
    try {
      const response = await fetch(getFullUrl('posts'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

export class PostsApi {
  static async getPosts(): Promise<Post[]> {
    const response = await fetch(getFullUrl('posts'), {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      return handleApiError(response);
    }

    return response.json();
  }

  static async createPost(post: CreatePostPayload): Promise<Post> {
    const response = await fetch(getFullUrl('posts'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(post),
    });

    if (!response.ok) {
      return handleApiError(response);
    }

    return response.json();
  }

  static async updatePost(id: number, post: UpdatePostPayload): Promise<Post> {
    const response = await fetch(getFullUrl(`posts/${id}`), {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(post),
    });

    if (!response.ok) {
      return handleApiError(response);
    }

    return response.json();
  }

  static async deletePost(id: number): Promise<void> {
    const response = await fetch(getFullUrl(`posts/${id}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      return handleApiError(response);
    }
  }

  static async postNow(id: number): Promise<Post> {
    const response = await fetch(getFullUrl(`posts/${id}`), {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status: 'post_now' }),
    });

    if (!response.ok) {
      return handleApiError(response);
    }

    return response.json();
  }

  static async uploadImage(file: File): Promise<ImageUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token is missing');
      }
      
      // Use the correct endpoint
      const uploadUrl = getFullUrl('upload');
      
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        return handleApiError(response);
      }

      return await response.json();
    } catch (error) {
      // Only log errors
      console.error("Image upload error:", error);
      throw error;
    }
  }
}