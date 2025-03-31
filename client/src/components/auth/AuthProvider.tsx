import React, { createContext, useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';

// Define types for the auth context
interface User {
  id: string;
  name: string;
  email: string;
  modules?: string[];
  username?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, password: string) => Promise<void>;
}

// Create the authentication context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth provider component
export const AuthProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Check if user is logged in on initial load and when token changes
  const fetchUserData = async () => {
    try {
      // Check if we have a token in localStorage
      const token = localStorage.getItem('auth_token');
      
      if (token) {
        // If we have a token, try to get the user data
        setIsLoading(true);
        const userData = await authService.getCurrentUser();
        setUser(userData.user);
      } else {
        // No token found
        setUser(null);
      }
    } catch (err) {
      console.error('Auth check failed:', err);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  // Login function
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
  
    try {
      const data = await authService.login(email, password);
      
      // Save token to localStorage
      if (data.token) {
        localStorage.setItem('auth_token', data.token);
        // Set user data directly from the login response
        setUser(data.user);
      }
      
      // We don't navigate here anymore - let the component handle that
      // This prevents form resets when errors occur
      return data; // Return data so the component knows login was successful
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err; // Re-throw to let component know login failed
    } finally {
      setIsLoading(false);
    }
  };

  // Signup function
  const signup = async (name: string, email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.signup(name, email, password);
      navigate('/login?registered=true');
    } catch (err: any) {
      setError(err.message || 'Signup failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.logout();
      
      // Remove token from localStorage
      localStorage.removeItem('auth_token');
      
      setUser(null);
      navigate('/login');
    } catch (err: any) {
      setError(err.message || 'Logout failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Forgot password function
  const forgotPassword = async (email: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.forgotPassword(email);
    } catch (err: any) {
      setError(err.message || 'Password reset request failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Reset password function
  const resetPassword = async (token: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.resetPassword(token, password);
    } catch (err: any) {
      setError(err.message || 'Password reset failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // The context value
  const value = {
    user,
    isLoading,
    error,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider;