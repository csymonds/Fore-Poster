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
}

export interface CreatePostPayload {
  content: string;
  scheduled_time: string;
  platform: string;
  status: Post['status']; // Required, will always be set to 'draft' by default
}

export interface UpdatePostPayload {
  content?: string;
  scheduled_time?: string;
  platform?: string;
  status?: Post['status'];
}

interface ApiError {
  error: string;
  status?: number;
  details?: any;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

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
    const response = await fetch(`${API_BASE_URL}/login`, {
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
  }

  static async validateToken(token: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/posts`, {
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
    const response = await fetch(`${API_BASE_URL}/posts`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      return handleApiError(response);
    }

    return response.json();
  }

  static async createPost(post: CreatePostPayload): Promise<Post> {
    const response = await fetch(`${API_BASE_URL}/posts`, {
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
    const response = await fetch(`${API_BASE_URL}/posts/${id}`, {
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
    const response = await fetch(`${API_BASE_URL}/posts/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      return handleApiError(response);
    }
  }

  static async postNow(id: number): Promise<Post> {
    const response = await fetch(`${API_BASE_URL}/posts/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status: 'post_now' }),
    });

    if (!response.ok) {
      return handleApiError(response);
    }

    return response.json();
  }
}