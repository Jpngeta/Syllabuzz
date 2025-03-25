import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, User, UserPlus } from 'lucide-react';
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

const SignupForm: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [formErrors, setFormErrors] = useState<{[key: string]: string}>({});
  
  const { signup, isLoading, error } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    setFormData(prev => ({
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

    // Password strength check if the password field is being updated
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
    
    // Validate name
    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }
    
    // Validate email
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
    }
    
    // Validate password
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (passwordStrength < 2) {
      errors.password = 'Password is too weak';
    }
    
    // Validate password confirmation
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    // Validate terms agreement
    if (!agreedToTerms) {
      errors.terms = 'You must agree to the terms and conditions';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    try {
      await signup(formData.name, formData.email, formData.password);
      // On success, the user will be redirected to login by the AuthProvider
    } catch (err) {
      // Error is handled in the AuthProvider
      console.error('Signup error:', err);
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
          <p style={{ color: darkColors.textSecondary }}>Create your account</p>
        </div>

        <div className="border-2 rounded-lg shadow-md p-6 bg-white"
          style={{ borderColor: darkColors.primary, backgroundColor: darkColors.surface }}
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-center title-font" style={{ color: darkColors.primary }}>
              Get Started
            </h2>
            <p className="text-center text-sm mt-1" style={{ color: darkColors.textSecondary }}>
              Create your account to start exploring
            </p>
          </div>
          
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
              <label htmlFor="name" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  id="name"
                  name="name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  style={{ 
                    borderColor: formErrors.name ? '#FF5252' : darkColors.primary,
                    color: darkColors.textPrimary
                  }}
                  required
                />
              </div>
              {formErrors.name && (
                <p className="text-xs mt-1" style={{ color: '#FF5252' }}>{formErrors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  style={{ 
                    borderColor: formErrors.email ? '#FF5252' : darkColors.primary,
                    color: darkColors.textPrimary
                  }}
                  required
                />
              </div>
              {formErrors.email && (
                <p className="text-xs mt-1" style={{ color: '#FF5252' }}>{formErrors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium" style={{ color: darkColors.textPrimary }}>
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full pl-10 py-2 border-2 rounded-md focus:outline-none focus:ring-2 focus:border-transparent transition-all"
                  style={{ 
                    borderColor: formErrors.password ? '#FF5252' : darkColors.primary,
                    color: darkColors.textPrimary
                  }}
                  required
                />
              </div>
              {formData.password && (
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
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={formData.confirmPassword}
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

            <div className="flex items-center space-x-2">
              <input 
                id="terms" 
                type="checkbox"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
                style={{ accentColor: darkColors.primary }}
              />
              <label
                htmlFor="terms"
                className="text-sm font-medium"
                style={{ color: formErrors.terms ? '#FF5252' : darkColors.textSecondary }}
              >
                I agree to the{" "}
                <Link to="/terms" className="hover:underline" style={{ color: darkColors.primary }}>
                  terms of service
                </Link>
                {" "}and{" "}
                <Link to="/privacy" className="hover:underline" style={{ color: darkColors.primary }}>
                  privacy policy
                </Link>
              </label>
            </div>
            {formErrors.terms && (
              <p className="text-xs mt-1" style={{ color: '#FF5252' }}>{formErrors.terms}</p>
            )}

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
                  <UserPlus className="w-4 h-4" />
                  Create Account
                </>
              )}
            </button>
          </form>
          
          <div className="mt-6 pt-4 border-t" style={{ borderColor: darkColors.border }}>
            <p className="text-center text-sm" style={{ color: darkColors.textSecondary }}>
              Already have an account?{" "}
              <Link to="/login" className="font-semibold hover:underline" style={{ color: darkColors.primary }}>
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupForm;