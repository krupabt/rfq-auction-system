import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AlertCircle, Eye, EyeOff, X } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);

  // Load remembered email on mount
  useEffect(() => {
    const savedEmail = localStorage.getItem('rfq_remember_email');
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      // 1. Authenticate using registered email and password
      const loggedUser = await login(email.trim(), password);

      // 2. Handle Remember Me preference
      if (rememberMe) {
        localStorage.setItem('rfq_remember_email', email.trim());
      } else {
        localStorage.removeItem('rfq_remember_email');
      }

      // 3. Automatically identify role and redirect to correct dashboard
      if (loggedUser.role === 'SUPPLIER') {
        navigate('/auctions');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 403) {
        setError(detail || 'Your account is pending administrator approval or inactive.');
      } else if (status === 401) {
        setError('Invalid email or password.');
      } else {
        setError(detail || 'Authentication failed. Please check your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillDemo = (demoEmail: string, demoPassword: string) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 text-[#111111] font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        {/* Page Title & Subtitle */}
        <div className="text-center mb-6">
          <h1 className="text-[24px] font-semibold text-[#111111] tracking-tight">
            RFQ & British Auction
          </h1>
          <p className="text-[14px] text-[#777777] mt-1 font-normal">
            Sign in to continue
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white p-8 border border-[#E5E5E5] rounded-[4px]">
          {error && (
            <div className="mb-4 p-3 border border-red-200 bg-red-50/50 rounded-[4px] text-[13px] text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email Address */}
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                autoComplete="email"
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111] transition-colors"
                required
              />
            </div>

            {/* Password with Show/Hide Option */}
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full pl-3 pr-10 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111] transition-colors"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#777777] hover:text-[#111111] focus:outline-none cursor-pointer"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between text-[13px] pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-[#E5E5E5] text-[#111111] focus:ring-0 cursor-pointer accent-[#111111]"
                />
                <span className="text-[#777777]">Remember me</span>
              </label>

              <button
                type="button"
                onClick={() => setShowForgotModal(true)}
                className="text-[#777777] hover:text-[#111111] hover:underline cursor-pointer"
              >
                Forgot password?
              </button>
            </div>

            {/* Black Sign In Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-[#111111] hover:bg-black disabled:bg-[#888888] text-white rounded-[4px] text-[14px] font-medium transition-colors cursor-pointer mt-2"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Demo Login Credentials Section */}
          <div className="mt-6 pt-5 border-t border-[#E5E5E5]">
            <h2 className="text-[12px] font-semibold uppercase tracking-wider text-[#777777] mb-2.5">
              Demo Login Credentials
            </h2>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleFillDemo('admin@demo.com', 'admin123')}
                className="py-1.5 px-2 text-[12px] font-medium text-[#111111] bg-white border border-[#E5E5E5] hover:border-[#111111] hover:bg-[#FAFAFA] rounded-[4px] transition-colors text-center cursor-pointer"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('buyer@demo.com', 'buyer123')}
                className="py-1.5 px-2 text-[12px] font-medium text-[#111111] bg-white border border-[#E5E5E5] hover:border-[#111111] hover:bg-[#FAFAFA] rounded-[4px] transition-colors text-center cursor-pointer"
              >
                Buyer
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('supplier@demo.com', 'supplier123')}
                className="py-1.5 px-2 text-[12px] font-medium text-[#111111] bg-white border border-[#E5E5E5] hover:border-[#111111] hover:bg-[#FAFAFA] rounded-[4px] transition-colors text-center cursor-pointer"
              >
                Supplier
              </button>
            </div>
            <p className="text-[11px] text-[#777777] mt-2 text-center">
              Clicking a button fills the credentials. Click <strong>Sign In</strong> to log in.
            </p>
          </div>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="bg-white rounded-[4px] border border-[#E5E5E5] max-w-sm w-full p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-3">
              <h3 className="text-[16px] font-semibold text-[#111111]">
                Forgot Password
              </h3>
              <button
                type="button"
                onClick={() => setShowForgotModal(false)}
                className="text-[#777777] hover:text-[#111111] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-[13px] text-[#777777] leading-relaxed">
              Please contact your system administrator at{' '}
              <strong className="text-[#111111]">admin@demo.com</strong> to reset your password.
            </p>

            <button
              type="button"
              onClick={() => setShowForgotModal(false)}
              className="w-full py-2 bg-[#111111] hover:bg-black text-white text-[13px] font-medium rounded-[4px] transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
