import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export const UserManagementPage: React.FC = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Add User modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUserName, setNewUserName] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newUserRole, setNewUserRole] = useState<'ADMIN' | 'BUYER' | 'SUPPLIER'>('BUYER');
  const [newUserCompany, setNewUserCompany] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);

  // Role Assignment modal state
  const [roleModalUser, setRoleModalUser] = useState<any>(null);
  const [selectedRole, setSelectedRole] = useState<string>('BUYER');

  const fetchUsers = async () => {
    try {
      const res = await api.get('/auth/admin/users');
      setUsers(res.data);
    } catch (err) {
      console.error('Failed to load users', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await api.patch(`/auth/admin/users/${userId}/status`, { is_active: !currentStatus });
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user status.');
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await api.patch(`/auth/admin/users/${userId}/role`, { role: newRole });
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update user role.');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
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
      fetchUsers();
      setTimeout(() => setShowCreateModal(false), 1000);
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create user account.');
    }
  };

  const formatRole = (role: string) => {
    if (role === 'ADMIN') return 'Admin';
    if (role === 'BUYER') return 'Buyer';
    if (role === 'SUPPLIER') return 'Supplier';
    return role;
  };

  return (
    <div className="space-y-6">
      {/* Header & Add User button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#111111]">User Management</h1>
          <p className="text-sm text-[#777777] mt-1">
            Manage system users, assign roles, and activate or deactivate accounts.
          </p>
        </div>
        <button
          onClick={() => {
            setCreateError(null);
            setCreateSuccess(null);
            setShowCreateModal(true);
          }}
          className="px-3.5 py-2 bg-[#111111] hover:bg-black text-white text-xs font-medium rounded-[4px] cursor-pointer"
        >
          + Add User
        </button>
      </div>

      {/* User Table */}
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
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-6 px-4 text-center text-[#777777]">
                  Loading users...
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 px-4 text-center text-[#777777]">
                  No users found.
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className="hover:bg-[#FAFAFA]">
                  <td className="py-2.5 px-4 font-medium text-[#111111]">
                    {u.full_name}
                  </td>
                  <td className="py-2.5 px-4 text-[#777777] font-mono">
                    {u.email}
                  </td>
                  <td className="py-2.5 px-4 font-medium text-[#111111]">
                    {formatRole(u.role)}
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
                      onClick={() => handleToggleStatus(u.id, u.is_active)}
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

      {/* Add User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-[4px] border border-[#E5E5E5] max-w-sm w-full p-5 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-2">
              <h3 className="text-sm font-semibold text-[#111111]">Add User</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
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

            <form onSubmit={handleCreateUser} className="space-y-3">
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
                  placeholder="e.g. alice@demo.com"
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
                    placeholder="e.g. Demo Freight"
                    className="w-full px-2.5 py-1.5 text-xs border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                </div>
              )}

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
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

      {/* Change Role Modal */}
      {roleModalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-[4px] border border-[#E5E5E5] max-w-xs w-full p-5 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-[#E5E5E5] pb-2">
              <h3 className="text-sm font-semibold text-[#111111]">Change Role</h3>
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
    </div>
  );
};
