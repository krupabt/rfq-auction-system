import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  FileText,
  Gavel,
  Users,
  BarChart2,
  List,
  Settings,
  LogOut,
  Bell,
  User,
  Plus,
} from 'lucide-react';
import api from '../services/api';

export const AppLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isReseeding, setIsReseeding] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleResetData = async () => {
    if (window.confirm('Reset database to default sample auctions and suppliers?')) {
      setIsReseeding(true);
      try {
        await api.post('/seed?force=true');
        alert('Database reset completed.');
        window.location.reload();
      } catch (err: any) {
        alert(err.message || 'Reset failed');
      } finally {
        setIsReseeding(false);
      }
    }
  };

  const isBuyerOrAdmin = user?.role === 'BUYER' || user?.role === 'ADMIN';

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    ...(isBuyerOrAdmin ? [{ label: 'RFQs', path: '/rfqs', icon: FileText }] : []),
    { label: 'Auctions', path: '/auctions', icon: Gavel },
    ...(user?.role === 'ADMIN' ? [{ label: 'User Management', path: '/users', icon: Users }] : []),
    { label: 'Suppliers', path: '/suppliers', icon: Users },
    { label: 'Reports', path: '/reports', icon: BarChart2 },
    { label: 'Activity Logs', path: '/activity-logs', icon: List },
  ];

  const getPageInfo = () => {
    const p = location.pathname;
    if (p.startsWith('/dashboard')) return { title: 'Dashboard', breadcrumb: 'Home / Dashboard' };
    if (p === '/rfqs/new') return { title: 'Create RFQ', breadcrumb: 'Home / RFQs / Create' };
    if (p.startsWith('/rfqs')) return { title: 'RFQs', breadcrumb: 'Home / RFQs' };
    if (p.startsWith('/auctions/')) return { title: 'Auction Details', breadcrumb: 'Home / Auctions / Details' };
    if (p === '/auctions') return { title: 'Auctions', breadcrumb: 'Home / Auctions' };
    if (p === '/active-auctions') return { title: 'Active Auctions', breadcrumb: 'Home / Auctions / Active' };
    if (p === '/suppliers') return { title: 'Suppliers', breadcrumb: 'Home / Suppliers' };
    if (p === '/users') return { title: 'User Management', breadcrumb: 'Home / User Management' };
    if (p === '/reports') return { title: 'Reports', breadcrumb: 'Home / Reports' };
    if (p === '/activity-logs') return { title: 'Activity Logs', breadcrumb: 'Home / Activity Logs' };
    return { title: 'Dashboard', breadcrumb: 'Home' };
  };

  const { title, breadcrumb } = getPageInfo();

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-white text-[#111111] font-sans">
      {/* 1. Left Sidebar: Fixed full height */}
      <aside className="w-64 h-full bg-white border-r border-[#E5E5E5] flex flex-col justify-between shrink-0 select-none z-30">
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          {/* Logo: RFQ */}
          <div className="h-16 flex items-center px-6 border-b border-[#E5E5E5] shrink-0">
            <div
              className="cursor-pointer flex items-center gap-2"
              onClick={() => navigate('/dashboard')}
            >
              <span className="text-xl font-bold tracking-tight text-[#111111]">
                RFQ
              </span>
              <span className="text-xs font-medium text-[#777777] border-l border-[#E5E5E5] pl-2">
                British Auction
              </span>
            </div>
          </div>

          {/* Quick Create Action for Buyers/Admins */}
          {isBuyerOrAdmin && (
            <div className="p-4 border-b border-[#E5E5E5] shrink-0">
              <button
                onClick={() => navigate('/rfqs/new')}
                className="w-full h-9 bg-[#111111] hover:bg-black text-white text-sm font-medium rounded-[4px] flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Create RFQ</span>
              </button>
            </div>
          )}

          {/* Navigation Links (Scrollable if list expands) */}
          <nav className="flex-1 overflow-y-auto p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-[4px] text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-[#F5F5F5] text-[#111111] font-semibold'
                        : 'text-[#777777] hover:text-[#111111] hover:bg-[#FAFAFA]'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0 text-[#777777]" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Bottom: User Profile & Clearly Visible Logout Button */}
        <div className="shrink-0 border-t border-[#E5E5E5] p-4 pb-5 space-y-3 bg-[#FAFAFA]/70">
          {/* User Profile Card */}
          <div className="bg-white border border-[#E5E5E5] rounded-[6px] p-3 shadow-xs">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-[#111111] truncate">
                {user?.full_name}
              </span>
              <span className="inline-block px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-[3px] border border-[#E5E5E5] bg-[#F5F5F5] text-[#111111] shrink-0">
                {user?.role}
              </span>
            </div>
            <div className="text-xs text-[#777777] font-mono truncate mt-1" title={user?.email}>
              {user?.email}
            </div>
            {user?.supplier_profile?.company_name && (
              <div className="text-[11px] text-[#555555] truncate mt-0.5" title={user.supplier_profile.company_name}>
                {user.supplier_profile.company_name}
              </div>
            )}
          </div>

          {/* Reset Sample Data Button */}
          <button
            onClick={handleResetData}
            disabled={isReseeding}
            className="w-full text-left text-xs font-medium text-[#777777] hover:text-[#111111] px-2 py-1.5 rounded-[4px] hover:bg-[#F0F0F0] flex items-center gap-2 transition-colors cursor-pointer"
          >
            <Settings className="w-3.5 h-3.5" />
            <span>{isReseeding ? 'Resetting...' : 'Reset Sample Data'}</span>
          </button>

          {/* Dedicated, Centered, High-Contrast Logout Button */}
          <button
            onClick={handleLogout}
            className="w-full h-9 flex items-center justify-center gap-2 px-3 bg-white border border-[#111111] hover:bg-[#111111] text-[#111111] hover:text-white text-xs font-semibold rounded-[4px] transition-colors cursor-pointer shadow-xs"
            title="Log out of your account"
          >
            <LogOut className="w-3.5 h-3.5 shrink-0" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* 2. Main Content Container: Scrolls independently */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-white overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="h-16 bg-white border-b border-[#E5E5E5] px-8 flex items-center justify-between shrink-0 sticky top-0 z-20">
          <div>
            <div className="text-xs font-normal text-[#777777]">
              {breadcrumb}
            </div>
            <div className="text-base font-semibold text-[#111111] mt-0.5">
              {title}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              className="p-2 text-[#777777] hover:text-[#111111] rounded-[4px] hover:bg-[#F5F5F5] transition-colors cursor-pointer relative"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="w-1.5 h-1.5 rounded-full bg-[#16A34A] absolute top-2 right-2" />
            </button>

            <div className="flex items-center gap-2 pl-3 border-l border-[#E5E5E5] text-xs font-medium text-[#111111]">
              <User className="w-4 h-4 text-[#777777]" />
              <span>{user?.email}</span>
            </div>
          </div>
        </header>

        {/* Page Content: Scrolls independently */}
        <main className="flex-1 overflow-y-auto p-8 max-w-6xl w-full mx-auto bg-white">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
