import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DevTestAccountsPage } from './pages/DevTestAccountsPage';
import { DashboardPage } from './pages/DashboardPage';
import { RFQManagementPage } from './pages/RFQManagementPage';
import { CreateRFQPage } from './pages/CreateRFQPage';
import { AuctionListingPage } from './pages/AuctionListingPage';
import { ActiveAuctionsPage } from './pages/ActiveAuctionsPage';
import { AuctionDetailPage } from './pages/AuctionDetailPage';
import { SuppliersPage } from './pages/SuppliersPage';
import { ReportsPage } from './pages/ReportsPage';
import { ActivityLogsPage } from './pages/ActivityLogsPage';
import { UserManagementPage } from './pages/UserManagementPage';

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-xs">
        Loading procurement session...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dev-test-accounts" element={<DevTestAccountsPage />} />

          {/* Protected Application Layout routes */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/rfqs" element={<RFQManagementPage />} />
            <Route path="/rfqs/new" element={<CreateRFQPage />} />
            <Route path="/rfqs/:id" element={<AuctionDetailPage />} />
            <Route path="/auctions" element={<AuctionListingPage />} />
            <Route path="/active-auctions" element={<ActiveAuctionsPage />} />
            <Route path="/auctions/:id" element={<AuctionDetailPage />} />
            <Route path="/suppliers" element={<SuppliersPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/activity-logs" element={<ActivityLogsPage />} />
            <Route path="/users" element={<UserManagementPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
