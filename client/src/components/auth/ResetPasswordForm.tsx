import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, Lock, Shield, AlertTriangle } from 'lucide-react';
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
  error: '#FF5252',
};

const ResetPasswordForm: React.FC = () => {
  const [passwords, setPasswords] = useState({
    password: '',
    confirmPassword: '',
  });
  const [isSuccess, setIsSuccess] = useState(false);
  const [isValidToken, setIsValidToken] = useState(true);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [formErrors, setFormErrors] = useState<{[key: string]: string}>({});
  
  const { resetPassword, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract token from URL query parameters
  const searchParams = new URLSearchParams(location.search);
  const token = searchParams.get('token');

  useEffect(() => {
    // Verify token is valid on component mount
    const verifyToken = async () => {
      if (!token) {
        setIsValidToken(false);
        return;
      }
      
      try {
        // This would be a real API call in a production app
        const response = await fetch(`/api/auth/verify-reset-token?token=${token}`);
        if (!response.ok) {
          setIsValidToken(false);
        }
      } catch (err) {
        setIsValidToken(false);
      }
    };

    verifyToken();
  }, [token]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    setPasswords(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Reset field-specific error when user types
    if (formErrors[name]) {
      setFormErrors(prev => {
        const newErrors = {...prev};
        delete newErrors[name];
        return newErrors;
      });
    }

    // Check password strength if the password field is being updated
    if (name === 'password') {
      checkPasswordStrength(value);
    }
  };

  const checkPasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    setPasswordStrength(strength);
  };

  const getStrengthText = () => {
    if (passwordStrength === 0) return "Weak";
    if (passwordStrength === 1) return "Fair";
    if (passwordStrength === 2) return "Good";
    if (passwordStrength === 3) return "Strong";
    return "Very strong";
  };

  const getStrengthColor = () => {
    const colors = ['#FF5252', '#FFB100', '#FFD166', '#06D6A0', '#00BB9F'];
    return colors[passwordStrength] || colors[0];
  };
  
  const validateForm = () => {
    const errors: {[key: string]: string} = {};
    
    // Validate password
    if (!passwords.password) {
      errors.password = 'Password is required';
    } else if (passwordStrength < 2) {
      errors.password = 'Password is too weak';
    }
    
    // Validate password confirmation
    if (passwords.password !== passwords.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !token) {
      return;
    }
    
    try {
      await resetPassword(token, passwords.password);
      setIsSuccess(true);
      
      // Redirect to login after a delay
      setTimeout(() => {
        navigate('/login?reset=success');
      }, 3000);
    } catch (err) {
      // Error is handled in the AuthProvider
      console.error('Reset password error:', err);
    }
  };

  // If no token is provided
  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-white to-gray-100 p-4">
        <div className="w-full max-w-md">
          <div className="border-2 rounded-lg shadow-md p-6 bg-white"
            style={{ borderColor: darkColors.error, backgroundColor: darkColors.surface }}
          >
            <div className="flex flex-col items-center">
              <AlertTriangle size={48} className="mb-4" style={{ color: darkColors.error }} />
              <h2 className="text-xl font-bold mb-2" style={{ color: darkColors.error }}>Invalid Request</h2>
              <p className="text-center mb-6" style={{ color: darkColors.textSecondary }}>
                No reset token provided. Please request a new password reset link.
              </p>
              <Link 
                to="/forgot-password" 
                className="py-2 px-4 rounded-md font-medium text-white transition-all"
                style={{ backgroundColor: darkColors.primary }}
              >
                Go to Forgot Password
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // If token is invalid
  if (!isValidToken) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-white to-gray-100 p-4">
        <div className="w-full max-w-md">
          <div className="border-2 rounded-lg shadow-md p-6 bg-white"
            style={{ borderColor: darkColors.error, backgroundColor: darkColors.surface }}
          >
            <div className="flex flex-col items-center">
              <AlertTriangle size={48} className="mb-4" style={{ color: darkColors.error }} />
              <h2 className="text-xl font-bold mb-2" style={{ color: darkColors.error }}>Invalid or Expired Token</h2>
              <p className="text-center mb-6" style={{ color: darkColors.textSecondary }}>
                This password reset link is invalid or has expired. Please request a new one.
              </p>
              <Link 
                to="/forgot-password" 
                className="py-2 px-4 rounded-md font-medium text-white transition-all"
                style={{ backgroundColor: darkColors.primary }}
              >
                Request New Reset Link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
          <p style={{ color: darkColors.textSecondary }}>Set your new password</p>
        </div>

        <div className="border-2 rounded-lg shadow-md p-6 bg-white"
          style={{ borderColor: darkColors.primary, backgroundColor: darkColors.surface }}
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-center title-font" style={{ color: darkColors.primary }}>
              Reset Password
            </h2>
            <p className="text-center text-sm mt-1" style={{ color: darkColors.textSecondary }}>
              Choose a new strong password for your account
            </p>
          </div>
          
          {isSuccess ? (
            <div className="p-4 rounded-md border-2"
              style={{ 
                borderColor: darkColors.success, 
                backgroundColor: `${darkColors.success}20` 
              }}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: darkColors.success }}>Password Reset Successfully!</h3>
              <p className="text-sm">
                Your password has been changed. You will be redirected to the login page shortly.
              </p>
              <div className="mt-6 text-center">
                <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent" style={{ color: darkColors.success }}></div>
                <span className="ml-2 text-sm" style={{ color: darkColors.textSecondary }}>Redirecting...</span>
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
                <label htmlFor="password" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                  New Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    value={passwords.password}
                    onChange={handleChange}
                    className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                    style={{ 
                      borderColor: formErrors.password ? '#FF5252' : darkColors.primary,
                      color: darkColors.textPrimary
                    }}
                    required
                  />
                </div>
                {passwords.password && (
                  <div className="mt-1">
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span>Password strength:</span>
                      <span style={{ color: getStrengthColor() }}>{getStrengthText()}</span>
                    </div>
                    <div className="w-full h-1 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full transition-all duration-300 ease-in-out" 
                        style={{ 
                          width: `${(passwordStrength / 4) * 100}%`,
                          backgroundColor: getStrengthColor()
                        }}
                      ></div>
                    </div>
                  </div>
                )}
                {formErrors.password && (
                  <p className="text-xs mt-1" style={{ color: '#FF5252' }}>{formErrors.password}</p>
                )}
              </div>

              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                  Confirm New Password
                </label>
                <div className="relative">
                  <Shield className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={passwords.confirmPassword}
                    onChange={handleChange}
                    className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                    style={{ 
                      borderColor: formErrors.confirmPassword ? '#FF5252' : darkColors.primary,
                      color: darkColors.textPrimary
                    }}
                    required
                  />
                </div>
                {formErrors.confirmPassword && (
                  <p className="text-xs mt-1" style={{ color: '#FF5252' }}>{formErrors.confirmPassword}</p>
                )}
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
                    <Lock className="w-4 h-4" />
                    Reset Password
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

export default ResetPasswordForm;