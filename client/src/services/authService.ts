import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token in requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle unauthorized errors (token expired, etc.)
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication service
export const authService = {
  // Login user and get token
  login: async (email: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      // Store token in localStorage for future requests
      if (response.data.token) {
        localStorage.setItem('auth_token', response.data.token);
      }
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Login failed');
      }
      throw new Error('Login failed. Please check your connection.');
    }
  },

  // Register a new user
  signup: async (name: string, email: string, password: string) => {
    try {
      const response = await api.post('/auth/signup', { name, email, password });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Signup failed');
      }
      throw new Error('Signup failed. Please check your connection.');
    }
  },

  // Logout user (clear token)
  logout: async () => {
    try {
      const response = await api.post('/auth/logout');
      // Always remove token from localStorage
      localStorage.removeItem('auth_token');
      return response.data;
    } catch (error) {
      // Always clear local token regardless of server response
      console.error('Logout error:', error);
      localStorage.removeItem('auth_token');
      // Still return success even if API call fails
      return { message: 'Logged out successfully' };
    }
  },

  // Request password reset
  forgotPassword: async (email: string) => {
    try {
      const response = await api.post('/auth/forgot-password', { email });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Password reset request failed');
      }
      throw new Error('Password reset request failed. Please check your connection.');
    }
  },

  // Reset password with token
  resetPassword: async (token: string, password: string) => {
    try {
      const response = await api.post('/auth/reset-password', { token, password });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Password reset failed');
      }
      throw new Error('Password reset failed. Please check your connection.');
    }
  },

  // Get current user data
  getCurrentUser: async () => {
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response && error.response.status !== 401) {
        // We don't throw for 401 as it's handled by the interceptor
        throw new Error(error.response.data.message || 'Failed to get user data');
      }
      throw new Error('Failed to get user data. Please check your connection.');
    }
  },

  // Verify reset token validity
  verifyResetToken: async (token: string) => {
    try {
      const response = await api.get(`/auth/verify-reset-token?token=${token}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Invalid or expired token');
      }
      throw new Error('Token verification failed. Please check your connection.');
    }
  },

  // =========== Article Interaction Methods ===========

  // Like an article
  likeArticle: async (articleId: string, moduleId?: string) => {
    try {
      const response = await api.post('/auth/like', { 
        article_id: articleId, 
        module_id: moduleId 
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to like article');
      }
      throw new Error('Failed to like article. Please check your connection.');
    }
  },

  // Save/bookmark an article
  bookmarkArticle: async (articleId: string, moduleId?: string) => {
    try {
      const response = await api.post('/auth/bookmark', { 
        article_id: articleId, 
        module_id: moduleId 
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to save article');
      }
      throw new Error('Failed to save article. Please check your connection.');
    }
  },

  // Remove a bookmark
  removeBookmark: async (articleId: string) => {
    try {
      const response = await api.delete(`/auth/bookmark/${articleId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to remove saved article');
      }
      throw new Error('Failed to remove saved article. Please check your connection.');
    }
  },

  // Get all bookmarked articles
  getBookmarks: async (limit: number = 20, skip: number = 0) => {
    try {
      const response = await api.get(`/auth/bookmarks?limit=${limit}&skip=${skip}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to get saved articles');
      }
      throw new Error('Failed to get saved articles. Please check your connection.');
    }
  },

  // Check if user has bookmarked a specific article
  isArticleBookmarked: async (articleId: string) => {
    try {
      const response = await api.get(`/auth/bookmark/${articleId}/status`);
      return response.data.isBookmarked;
    } catch (error) {
      // If there's an error, assume it's not bookmarked
      return false;
    }
  },

  // =========== Module Starring Methods ===========

  // Star a module
  starModule: async (moduleId: string) => {
    try {
      const response = await api.post('/auth/star-module', { module_id: moduleId });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to star module');
      }
      throw new Error('Failed to star module. Please check your connection.');
    }
  },

  // Unstar a module
  unstarModule: async (moduleId: string) => {
    try {
      const response = await api.delete(`/auth/star-module/${moduleId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to unstar module');
      }
      throw new Error('Failed to unstar module. Please check your connection.');
    }
  },

  // Get all starred modules
  getStarredModules: async () => {
    try {
      const response = await api.get('/auth/starred-modules');
      return response.data.modules;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(error.response.data.message || 'Failed to get starred modules');
      }
      throw new Error('Failed to get starred modules. Please check your connection.');
    }
  },

  // Check if a module is starred
  isModuleStarred: async (moduleId: string) => {
    try {
      const response = await api.get(`/auth/star-module/${moduleId}/status`);
      return response.data.isStarred;
    } catch (error) {
      // If there's an error, assume it's not starred
      return false;
    }
  },

  // Check if the user is authenticated
  isAuthenticated: () => {
    return localStorage.getItem('auth_token') !== null;
  },

  // Get the authentication token
  getToken: () => {
    return localStorage.getItem('auth_token');
  }
};

export default api;