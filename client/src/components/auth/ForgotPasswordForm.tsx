import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail, Send } from 'lucide-react';
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
  success: '#06D6A0',
};

const ForgotPasswordForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  const { forgotPassword, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await forgotPassword(email);
      setIsSubmitted(true);
    } catch (err) {
      // Error is handled in the AuthProvider
      console.error('Forgot password error:', err);
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
          <p style={{ color: darkColors.textSecondary }}>Reset your password</p>
        </div>

        <div className="border-2 rounded-lg shadow-md p-6 bg-white"
          style={{ borderColor: darkColors.primary, backgroundColor: darkColors.surface }}
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-center title-font" style={{ color: darkColors.primary }}>
              Forgot Password
            </h2>
            <p className="text-center text-sm mt-1" style={{ color: darkColors.textSecondary }}>
              Enter your email and we'll send you a reset link
            </p>
          </div>
          
          {isSubmitted ? (
            <div className="p-4 rounded-md border-2"
              style={{ 
                borderColor: darkColors.success, 
                backgroundColor: `${darkColors.success}20` 
              }}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: darkColors.success }}>Check your email</h3>
              <p className="text-sm">
                We've sent a password reset link to <span className="font-semibold">{email}</span>. Please check your inbox and follow the instructions to reset your password.
              </p>
              <div className="mt-6 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1 text-sm font-medium hover:underline"
                  style={{ color: darkColors.primary }}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Login
                </Link>
              </div>
            </div>
          ) : (
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

              <button
                type="submit"
                className="w-full py-2 px-4 rounded-md font-bold text-white transition-all hover:shadow-lg flex items-center justify-center gap-2 mt-6"
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
                    <Send className="w-4 h-4" />
                    Send Reset Link
                  </>
                )}
              </button>
              
              <div className="pt-4 text-center">
                <Link 
                  to="/login" 
                  className="inline-flex items-center gap-1 text-sm font-medium hover:underline" 
                  style={{ color: darkColors.primary }}
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Login
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordForm;