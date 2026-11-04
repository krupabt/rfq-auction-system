import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { AlertCircle, CheckCircle2, ArrowLeft, ShieldCheck, Building2, User, Mail, Lock, Phone, MapPin } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  const [role, setRole] = useState<'BUYER' | 'SUPPLIER'>('SUPPLIER');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Enterprise details
  const [companyName, setCompanyName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [responseMsg, setResponseMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const payload = {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        role,
        company_name: role === 'SUPPLIER' ? companyName.trim() : (companyName.trim() || undefined),
        contact_person: fullName.trim(),
        phone: phone.trim() || undefined,
        address: address.trim() || undefined,
      };

      const res = await api.post('/auth/register', payload);
      setIsSubmitted(true);
      setResponseMsg(res.data.message || 'Account request submitted successfully.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Account request failed. Please check your information and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FBFBFB] flex flex-col justify-between text-[#111111] font-sans">
      {/* Header */}
      <header className="w-full bg-white border-b border-[#E5E5E5] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/login" className="flex items-center gap-2">
            <span className="font-bold text-[18px] tracking-tight text-[#111111]">
              GoComet
            </span>
            <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 bg-[#111111] text-white rounded-[3px]">
              Access Request
            </span>
          </Link>
        </div>
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#777777] hover:text-[#111111] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Sign In</span>
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-lg space-y-6">
          {/* Title */}
          <div className="text-center space-y-1">
            <h1 className="text-[24px] font-semibold tracking-tight text-[#111111]">
              Request Platform Access
            </h1>
            <p className="text-[14px] text-[#777777]">
              Submit your details for administrator review and account activation
            </p>
          </div>

          {/* Success Confirmation State */}
          {isSubmitted ? (
            <div className="bg-white border border-[#E5E5E5] rounded-[6px] p-8 text-center space-y-5 shadow-xs">
              <div className="w-12 h-12 mx-auto rounded-full bg-[#EBF7EE] border border-[#C3E6CB] flex items-center justify-center text-[#1E7E34]">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div className="space-y-2">
                <h2 className="text-[18px] font-semibold text-[#111111]">
                  Account Request Received
                </h2>
                <p className="text-[14px] text-[#555555] leading-relaxed max-w-sm mx-auto">
                  {responseMsg}
                </p>
              </div>

              <div className="p-4 bg-[#FAFAFA] border border-[#E5E5E5] rounded-[4px] text-left text-[12px] space-y-1.5 font-mono text-[#555555]">
                <div>Email: <strong>{email}</strong></div>
                <div>Requested Role: <strong>{role}</strong></div>
                <div>Status: <span className="text-[#B36200] font-semibold">Pending Administrator Approval</span></div>
              </div>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  className="w-full py-2.5 bg-[#111111] hover:bg-black text-white rounded-[4px] text-[14px] font-medium transition-colors"
                >
                  Return to Sign In Page
                </button>
              </div>
            </div>
          ) : (
            /* Registration Request Form */
            <div className="bg-white border border-[#E5E5E5] rounded-[6px] p-8 shadow-xs">
              {error && (
                <div className="mb-5 p-3.5 border border-red-200 bg-red-50/60 rounded-[4px] text-[13px] text-red-800 flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-red-600" />
                  <span className="leading-snug">{error}</span>
                </div>
              )}

              {/* Controlled Role Selector (Buyer or Supplier only - No Admin) */}
              <div className="mb-5">
                <label className="block text-[13px] font-medium text-[#111111] mb-2">
                  Requested Organization Role
                </label>
                <div className="grid grid-cols-2 gap-2 p-1 bg-[#F5F5F5] border border-[#E5E5E5] rounded-[4px]">
                  <button
                    type="button"
                    onClick={() => setRole('SUPPLIER')}
                    className={`py-2 rounded-[3px] text-[13px] font-medium transition-colors cursor-pointer ${
                      role === 'SUPPLIER'
                        ? 'bg-white text-[#111111] shadow-xs'
                        : 'text-[#777777] hover:text-[#111111]'
                    }`}
                  >
                    Supplier / Carrier
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('BUYER')}
                    className={`py-2 rounded-[3px] text-[13px] font-medium transition-colors cursor-pointer ${
                      role === 'BUYER'
                        ? 'bg-white text-[#111111] shadow-xs'
                        : 'text-[#777777] hover:text-[#111111]'
                    }`}
                  >
                    Buyer / Shipper
                  </button>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-[13px] font-medium text-[#111111] mb-1">
                    Contact Full Name *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#999999]">
                      <User className="w-4 h-4" />
                    </div>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Klaus Jensen"
                      className="w-full pl-9 pr-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[13px] font-medium text-[#111111] mb-1">
                    Corporate Business Email *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#999999]">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="klaus@company.com"
                      className="w-full pl-9 pr-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[13px] font-medium text-[#111111] mb-1">
                    Password *
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#999999]">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minimum 6 characters"
                      minLength={6}
                      className="w-full pl-9 pr-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                      required
                    />
                  </div>
                </div>

                {/* Company Name */}
                <div>
                  <label className="block text-[13px] font-medium text-[#111111] mb-1">
                    Company / Organization Name {role === 'SUPPLIER' ? '*' : '(Optional)'}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#999999]">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <input
                      type="text"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      placeholder={role === 'SUPPLIER' ? 'e.g. Apex Global Logistics' : 'e.g. Acme Industrial Imports'}
                      className="w-full pl-9 pr-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                      required={role === 'SUPPLIER'}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[13px] font-medium text-[#111111] mb-1">
                      Business Phone
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#999999]">
                        <Phone className="w-4 h-4" />
                      </div>
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+1 555-0199"
                        className="w-full pl-9 pr-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[13px] font-medium text-[#111111] mb-1">
                      Headquarters Address
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#999999]">
                        <MapPin className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        placeholder="City, Country"
                        className="w-full pl-9 pr-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-2.5 bg-[#111111] hover:bg-black disabled:bg-[#CCCCCC] text-white rounded-[4px] text-[14px] font-medium transition-colors cursor-pointer"
                  >
                    {isLoading ? 'Submitting request...' : 'Submit Account Request'}
                  </button>
                </div>
              </form>

              <div className="mt-6 pt-6 border-t border-[#E5E5E5] text-center text-[13px] text-[#777777]">
                Already have an approved account?{' '}
                <Link to="/login" className="font-medium text-[#111111] hover:underline cursor-pointer">
                  Sign In
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-4 px-6 text-center text-[12px] text-[#888888] border-t border-[#E5E5E5] bg-white">
        RFQ & British Auction System
      </footer>
    </div>
  );
};
