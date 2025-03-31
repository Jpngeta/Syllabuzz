import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Lock, Mail, LogIn } from 'lucide-react';
import { useAuth } from './AuthProvider';

// Define the dark theme colors for consistency with the main app
const darkColors = {
  primary: '#FF6B6B',
  secondary: '#4ECDC4',
  tertiary: '#FFD166',
  quaternary: '#6A0572',
  background: '#FFFFFF',
  surface: '#F7F9FC',
  textPrimary: '#2D3748',
  textSecondary: '#4A5568',
  textMuted: '#718096',
  border: '#E2E8F0',
};

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  
  const { login, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Get query parameters
  const searchParams = new URLSearchParams(location.search);
  const redirect = searchParams.get('redirect') || '/';
  const registered = searchParams.get('registered');
  const resetSuccess = searchParams.get('reset');

  useEffect(() => {
    if (registered === 'true') {
      setShowSuccess(true);
    }
  }, [registered]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(email, password);
      // Only navigate on success
      navigate(redirect);
    } catch (err) {
      // Error is already handled in the AuthProvider
      // We're just preventing the form reset by not doing anything here
      console.error('Login error:', err);
      // Values of email and password state will be preserved
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-white to-gray-100 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 
            className="text-4xl font-bold mb-2 title-font" 
            style={{ color: darkColors.primary, fontFamily: 'DynaPuff, sans-serif' }}
          >
            Syllabuzz
          </h1>
          <p style={{ color: darkColors.textSecondary }}>Sign in to your account</p>
        </div>

        <div className="border-2 rounded-lg shadow-md p-6 bg-white"
          style={{ borderColor: darkColors.primary, backgroundColor: darkColors.surface }}
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-center title-font" style={{ color: darkColors.primary }}>
              Welcome Back
            </h2>
            <p className="text-center text-sm mt-1" style={{ color: darkColors.textSecondary }}>
              Enter your credentials to access your account
            </p>
          </div>
          
          {/* Registration success message */}
          {showSuccess && (
            <div className="mb-4 p-3 rounded-md border-2 animate-pulse"
              style={{ borderColor: darkColors.secondary, backgroundColor: `${darkColors.secondary}20` }}
            >
              <p className="text-sm font-medium">
                {resetSuccess === 'success' 
                  ? 'Password has been reset successfully! You can now log in with your new password.'
                  : 'Account registered successfully! You can now log in with your credentials.'}
              </p>
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-md border-2 mb-4 animate-pulse"
                style={{ borderColor: darkColors.primary, backgroundColor: `${darkColors.primary}20` }}
              >
                <p className="text-sm font-medium">
                  {error}
                </p>
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  style={{ 
                    borderColor: darkColors.primary,
                    color: darkColors.textPrimary
                  }}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label htmlFor="password" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                  Password
                </label>
                <Link to="/forgot-password" className="text-xs font-medium hover:underline" style={{ color: darkColors.secondary }}>
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  style={{ 
                    borderColor: darkColors.primary,
                    color: darkColors.textPrimary
                  }}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-2 px-4 rounded-md font-bold text-white transition-all hover:shadow-lg flex items-center justify-center gap-2"
              style={{ 
                backgroundColor: darkColors.primary,
                color: 'white',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1
              }}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="animate-spin h-5 w-5 border-2 border-t-transparent rounded-full" />
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  Sign In
                </>
              )}
            </button>
          </form>
          
          <div className="mt-6 pt-4 border-t" style={{ borderColor: darkColors.border }}>
            <p className="text-center text-sm" style={{ color: darkColors.textSecondary }}>
              Don't have an account?{" "}
              <Link to="/signup" className="font-semibold hover:underline" style={{ color: darkColors.primary }}>
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;