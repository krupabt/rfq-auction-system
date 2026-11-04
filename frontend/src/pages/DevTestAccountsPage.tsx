import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, ArrowLeft, AlertCircle, CheckCircle2, UserCheck } from 'lucide-react';

export const DevTestAccountsPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loadingEmail, setLoadingEmail] = useState<string | null>(null);

  const handleDevLogin = async (email: string, pass: string) => {
    setError(null);
    setLoadingEmail(email);
    try {
      const user = await login(email, pass);
      if (user.role === 'SUPPLIER') {
        navigate('/auctions');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed for test account.');
    } finally {
      setLoadingEmail(null);
    }
  };

  const testAccounts = [
    {
      category: 'System Roles',
      accounts: [
        {
          role: 'ADMIN',
          title: 'System Administrator',
          name: 'System Admin',
          email: 'admin@demo.com',
          pass: 'admin123',
          badge: 'Admin Access',
          dest: 'Dashboard & User Management'
        },
        {
          role: 'BUYER',
          title: 'Logistics Buyer',
          name: 'Procurement Buyer',
          email: 'buyer@demo.com',
          pass: 'buyer123',
          badge: 'RFQ Creation',
          dest: 'Dashboard & Live Auctions'
        }
      ]
    },
    {
      category: 'Suppliers (British Auction)',
      accounts: [
        {
          role: 'SUPPLIER',
          title: 'Supplier 1',
          name: 'Demo Ocean Carrier',
          email: 'supplier@demo.com',
          pass: 'supplier123',
          badge: 'Supplier Account',
          dest: 'Auction Bidding Room'
        },
        {
          role: 'SUPPLIER',
          title: 'Supplier 2: MSC Shipping',
          name: 'MSC Line Fleet',
          email: 'msc@carrier.com',
          pass: 'supplier123',
          badge: 'Competitive Challenger',
          dest: 'Auction Bidding Room'
        },
        {
          role: 'SUPPLIER',
          title: 'Supplier 3: Hapag-Lloyd',
          name: 'Hapag-Lloyd Global',
          email: 'hapag@carrier.com',
          pass: 'supplier123',
          badge: 'Competitive Challenger',
          dest: 'Auction Bidding Room'
        },
        {
          role: 'SUPPLIER',
          title: 'Supplier 4: CMA CGM Group',
          name: 'CMA CGM Freight',
          email: 'cmacgm@carrier.com',
          pass: 'supplier123',
          badge: 'Competitive Challenger',
          dest: 'Auction Bidding Room'
        }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto w-full space-y-6">
        {/* Navigation & Header */}
        <div className="flex items-center justify-between">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-[13px] font-medium text-[#777777] hover:text-[#111111] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Login</span>
          </Link>
          <span className="text-[12px] font-mono text-[#777777] bg-white border border-[#E5E5E5] px-2.5 py-1 rounded-[4px]">
            DEV_TEST_ENV: ACTIVE
          </span>
        </div>

        {/* Card Header */}
        <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-6 shadow-xs">
          <div className="flex items-start gap-4">
            <div className="p-2.5 bg-[#F5F5F5] border border-[#E5E5E5] rounded-[4px]">
              <Shield className="w-6 h-6 text-[#111111]" />
            </div>
            <div>
              <h1 className="text-[20px] font-semibold text-[#111111]">
                Developer & Evaluator Testing Environment
              </h1>
              <p className="text-[14px] text-[#777777] mt-1 leading-relaxed">
                This testing console is isolated from the production-facing login UI. Use these authenticated test accounts to simulate multi-party reverse auctions, Option C anti-sniping dynamic time extensions, and role-based permissions without manual credential entry.
              </p>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 border border-red-300 rounded-[4px] text-[13px] text-red-700 flex items-start gap-2 bg-red-50/50">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Account Categories */}
        {testAccounts.map((cat) => (
          <div key={cat.category} className="space-y-3">
            <h2 className="text-[13px] font-semibold uppercase tracking-wider text-[#777777]">
              {cat.category}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {cat.accounts.map((acc) => (
                <div
                  key={acc.email}
                  className="bg-white border border-[#E5E5E5] rounded-[4px] p-4 flex flex-col justify-between hover:border-[#111111] transition-colors"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 bg-[#F5F5F5] border border-[#E5E5E5] rounded-[4px] text-[#111111]">
                        {acc.role}
                      </span>
                      <span className="text-[11px] text-[#777777]">
                        {acc.badge}
                      </span>
                    </div>
                    <div className="text-[15px] font-semibold text-[#111111] pt-1">
                      {acc.title}
                    </div>
                    <div className="text-[12px] text-[#777777]">
                      {acc.name}
                    </div>
                    <div className="pt-2 font-mono text-[11px] text-[#555555] space-y-0.5 bg-[#FAFAFA] p-2 rounded-[4px] border border-[#EBEBEB]">
                      <div>Email: <strong>{acc.email}</strong></div>
                      <div>Password: <strong>{acc.pass}</strong></div>
                      <div className="text-[10px] text-[#888888]">Target: {acc.dest}</div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleDevLogin(acc.email, acc.pass)}
                    disabled={loadingEmail !== null}
                    className="mt-4 w-full py-2 bg-[#111111] hover:bg-black disabled:bg-[#CCCCCC] text-white rounded-[4px] text-[13px] font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    {loadingEmail === acc.email ? (
                      <span>Authenticating...</span>
                    ) : (
                      <>
                        <UserCheck className="w-4 h-4" />
                        <span>Sign In as {acc.role}</span>
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
