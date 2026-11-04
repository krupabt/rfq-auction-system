import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/StatusBadge';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [stats, setStats] = useState<any>(null);
  const [recentRfqs, setRecentRfqs] = useState<any[]>([]);
  const [recentActivities, setRecentActivities] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Admin User Management state
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [roleModalUser, setRoleModalUser] = useState<any>(null);
  const [selectedRole, setSelectedRole] = useState<string>('BUYER');
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newUserRole, setNewUserRole] = useState<'BUYER' | 'SUPPLIER' | 'ADMIN'>('BUYER');
  const [newUserCompany, setNewUserCompany] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);

  const fetchAdminUsers = async () => {
    if (user?.role === 'ADMIN') {
      try {
        const res = await api.get('/auth/admin/users');
        setAdminUsers(res.data);
      } catch (e) {
        console.error('Failed to load admin users', e);
      }
    }
  };

  const handleToggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await api.patch(`/auth/admin/users/${userId}/status`, { is_active: !currentStatus });
      fetchAdminUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user status.');
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await api.patch(`/auth/admin/users/${userId}/role`, { role: newRole });
      fetchAdminUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user role.');
    }
  };

  const handleAdminCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreateSuccess(null);
    try {
      await api.post('/auth/admin/users', {
        full_name: newUserName.trim(),
        email: newUserEmail.trim().toLowerCase(),
        password: newUserPassword,
        role: newUserRole,
        is_active: true,
        company_name: newUserRole === 'SUPPLIER' ? newUserCompany.trim() : undefined,
      });
      setCreateSuccess('User created successfully.');
      setNewUserName('');
      setNewUserEmail('');
      setNewUserPassword('');
      setNewUserCompany('');
      fetchAdminUsers();
      setTimeout(() => setShowCreateUserModal(false), 1000);
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create user account.');
    }
  };

  const fetchDashboard = async () => {
    try {
      const [statsRes, rfqsRes, actRes] = await Promise.all([
        api.get('/dashboard/stats'),
        api.get('/dashboard/recent-rfqs'),
        api.get('/dashboard/recent-activities'),
      ]);
      setStats(statsRes.data);
      setRecentRfqs(rfqsRes.data);
      setRecentActivities(actRes.data);
      if (user?.role === 'ADMIN') {
        fetchAdminUsers();
      }
    } catch (err) {
      console.error('Failed to load dashboard', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();

    // 1. WebSocket live updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/auctions`;
    let socket: WebSocket | null = null;
    try {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (['RFQ_CREATED', 'BID_SUBMITTED', 'DASHBOARD_UPDATE', 'AUCTION_EXTENDED'].includes(msg.type)) {
            fetchDashboard();
          }
        } catch (e) {
          // ignore
        }
      };
    } catch (e) {
      // ignore
    }

    // 2. Poll every 5s and re-fetch on window focus
    const interval = setInterval(fetchDashboard, 5000);
    window.addEventListener('focus', fetchDashboard);

    return () => {
      if (socket) socket.close();
      clearInterval(interval);
      window.removeEventListener('focus', fetchDashboard);
    };
  }, [user]);

  if (isLoading) {
    return <div className="text-sm text-[#777777] py-8">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Page Heading */}
      <div>
        <h1 className="text-2xl font-semibold text-[#111111]">Dashboard</h1>
        <p className="text-sm font-normal text-[#777777] mt-1">
          Overview of procurement RFQs, live British auctions and recent activities.
        </p>
      </div>

      {/* Four Small Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border border-[#E5E5E5] rounded-[4px] p-4 bg-white">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Total RFQs
          </div>
          <div className="text-2xl font-semibold text-[#111111] mt-1">
            {stats?.total_rfqs ?? 0}
          </div>
        </div>

        <div className="border border-[#E5E5E5] rounded-[4px] p-4 bg-white">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Active Auctions
          </div>
          <div className="text-2xl font-semibold text-[#111111] mt-1">
            {stats?.active_auctions ?? 0}
          </div>
        </div>

        <div className="border border-[#E5E5E5] rounded-[4px] p-4 bg-white">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Closed Auctions
          </div>
          <div className="text-2xl font-semibold text-[#111111] mt-1">
            {stats?.closed_auctions ?? 0}
          </div>
        </div>

        <div className="border border-[#E5E5E5] rounded-[4px] p-4 bg-white">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Total Bids
          </div>
          <div className="text-2xl font-semibold text-[#111111] mt-1">
            {stats?.total_bids_received ?? 0}
          </div>
        </div>
      </div>

      {/* Recent Auctions Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-[#111111]">Recent Auctions</h2>
          <button
            onClick={() => navigate('/auctions')}
            className="text-xs font-medium text-[#777777] hover:text-[#111111] underline cursor-pointer"
          >
            View all auctions
          </button>
        </div>

        <div className="border border-[#E5E5E5] rounded-[4px] overflow-hidden bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#FAFAFA] border-b border-[#E5E5E5] text-[#777777] text-xs font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4 font-semibold">RFQ ID</th>
                <th className="py-2.5 px-4 font-semibold">RFQ Name</th>
                <th className="py-2.5 px-4 font-semibold">Lowest Bid</th>
                <th className="py-2.5 px-4 font-semibold">Closing Time</th>
                <th className="py-2.5 px-4 font-semibold">Status</th>
                <th className="py-2.5 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide--[#E5E5E5]">
              {recentRfqs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 px-4 text-center text-xs text-[#777777]">
                    No recent auctions found.
                  </td>
                </tr>
              ) : (
                recentRfqs.map((rfq) => (
                  <tr key={rfq.id} className="hover:bg-[#FAFAFA] transition-colors">
                    <td className="py-3 px-4 font-mono text-xs font-medium text-[#111111]">
                      {rfq.reference_id}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-[#111111]">
                      {rfq.name}
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-[#111111]">
                      {rfq.lowest_bid ? `$${rfq.lowest_bid.toLocaleString()}` : <span className="text-[#777777]">—</span>}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-[#777777]">
                      {new Date(rfq.current_closing_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={rfq.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => navigate(`/auctions/${rfq.id}`)}
                        className="px-3 py-1 bg-white border border-[#111111] text-[#111111] hover:bg-neutral-50 text-xs font-medium rounded-[4px] cursor-pointer"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Small Recent Activity Section */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-[#111111]">Recent Activity</h2>
        <div className="border border-[#E5E5E5] rounded-[4px] divide-y divide-[#E5E5E5] bg-white">
          {recentActivities.length === 0 ? (
            <div className="py-6 px-4 text-center text-xs text-[#777777]">
              No recent activity logged.
            </div>
          ) : (
            recentActivities.map((act) => (
              <div key={act.id} className="py-3 px-4 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-[#777777] uppercase">
                    [{act.event_type.replace('_', ' ')}]
                  </span>
                  <span className="text-[#111111]">{act.description}</span>
                  {act.rfq_ref && (
                    <span className="font-mono text-[#777777]">({act.rfq_ref})</span>
                  )}
                </div>
                <span className="text-[#777777] font-mono shrink-0">
                  {new Date(act.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* User Management Section (Admin Only) */}
      {user?.role === 'ADMIN' && (
        <div className="space-y-4 pt-6 border-t border-[#E5E5E5]">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-[#111111]">User Management</h2>
              <p className="text-xs text-[#777777] mt-0.5">
                View registered users, assign roles, and activate or deactivate accounts.
              </p>
            </div>
            <button
              onClick={() => {
                setCreateError(null);
                setCreateSuccess(null);
                setShowCreateUserModal(true);
              }}
              className="px-3 py-1.5 bg-[#111111] hover:bg-black text-white text-xs font-medium rounded-[4px] cursor-pointer"
            >
              + Add User
            </button>
          </div>

          <div className="border border-[#E5E5E5] rounded-[4px] overflow-hidden bg-white">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAFAFA] border-b border-[#E5E5E5] text-[#777777] uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-4">Name</th>
                  <th className="py-2.5 px-4">Email</th>
                  <th className="py-2.5 px-4">Role</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5]">
                {adminUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 px-4 text-center text-[#777777]">
                      No users found.
                    </td>
                  </tr>
                ) : (
                  adminUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-[#FAFAFA]">
                      <td className="py-2.5 px-4 font-medium text-[#111111]">
                        {u.full_name}
                      </td>
                      <td className="py-2.5 px-4 text-[#777777] font-mono">
                        {u.email}
                      </td>
                      <td className="py-2.5 px-4 font-medium text-[#111111]">
                        {u.role === 'ADMIN' ? 'Admin' : u.role === 'BUYER' ? 'Buyer' : 'Supplier'}
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-[3px] text-[11px] font-medium ${
                            u.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-neutral-100 text-neutral-600'
                          }`}
                        >
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right space-x-2">
                        <button
                          onClick={() => {
                            setRoleModalUser(u);
                            setSelectedRole(u.role);
                          }}
                          className="px-2.5 py-1 text-[11px] font-medium rounded-[4px] border border-[#E5E5E5] bg-white text-[#111111] hover:bg-[#FAFAFA] cursor-pointer"
                        >
                          Change Role
                        </button>
                        <button
                          onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                          className={`px-2.5 py-1 text-[11px] font-medium rounded-[4px] border cursor-pointer ${
                            u.is_active
                              ? 'border-[#E5E5E5] bg-white text-red-600 hover:bg-red-50'
                              : 'border-[#111111] bg-[#111111] text-white hover:bg-black'
                          }`}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Change Role Modal */}
      {roleModalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-[4px] border border-[#E5E5E5] max-w-xs w-full p-5 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-2">
              <h3 className="text-sm font-semibold text-[#111111]">
                Change Role
              </h3>
              <button
                type="button"
                onClick={() => setRoleModalUser(null)}
                className="text-[#777777] hover:text-[#111111] text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-[#777777]">
              Assign role for <strong>{roleModalUser.full_name}</strong>:
            </p>

            <div>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] bg-white text-[#111111] focus:outline-none focus:border-[#111111] cursor-pointer"
              >
                <option value="ADMIN">Admin</option>
                <option value="BUYER">Buyer</option>
                <option value="SUPPLIER">Supplier</option>
              </select>
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => setRoleModalUser(null)}
                className="px-3 py-1.5 border border-[#E5E5E5] text-xs font-medium rounded-[4px] hover:bg-[#FAFAFA] cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={async () => {
                  await handleRoleChange(roleModalUser.id, selectedRole);
                  setRoleModalUser(null);
                }}
                className="px-3 py-1.5 bg-[#111111] hover:bg-black text-white text-xs font-medium rounded-[4px] cursor-pointer"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add User Modal */}
      {showCreateUserModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-[4px] border border-[#E5E5E5] max-w-sm w-full p-5 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-2">
              <h3 className="text-sm font-semibold text-[#111111]">
                Add User
              </h3>
              <button
                type="button"
                onClick={() => setShowCreateUserModal(false)}
                className="text-[#777777] hover:text-[#111111] text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            {createError && (
              <div className="p-2.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-[4px]">
                {createError}
              </div>
            )}
            {createSuccess && (
              <div className="p-2.5 bg-green-50 border border-green-200 text-green-800 text-xs rounded-[4px]">
                {createSuccess}
              </div>
            )}

            <form onSubmit={handleAdminCreateUser} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-[#111111] mb-1">Name</label>
                <input
                  type="text"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  placeholder="e.g. Alice Johnson"
                  className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#111111] mb-1">Email</label>
                <input
                  type="email"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  placeholder="e.g. alice@example.com"
                  className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#111111] mb-1">Password</label>
                <input
                  type="password"
                  value={newUserPassword}
                  onChange={(e) => setNewUserPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  minLength={6}
                  className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-[#111111] mb-1">Role</label>
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value as any)}
                  className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111] bg-white cursor-pointer"
                >
                  <option value="ADMIN">Admin</option>
                  <option value="BUYER">Buyer</option>
                  <option value="SUPPLIER">Supplier</option>
                </select>
              </div>

              {newUserRole === 'SUPPLIER' && (
                <div>
                  <label className="block text-xs font-medium text-[#111111] mb-1">Company Name</label>
                  <input
                    type="text"
                    value={newUserCompany}
                    onChange={(e) => setNewUserCompany(e.target.value)}
                    placeholder="e.g. Fast Logistics"
                    className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                </div>
              )}

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateUserModal(false)}
                  className="px-3 py-1.5 border border-[#E5E5E5] text-xs font-medium rounded-[4px] hover:bg-[#FAFAFA] cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-[#111111] hover:bg-black text-white text-xs font-medium rounded-[4px] cursor-pointer"
                >
                  Add User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
