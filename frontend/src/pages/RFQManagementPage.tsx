import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { Plus, Search } from 'lucide-react';

export const RFQManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  const fetchRfqs = async () => {
    try {
      const res = await api.get('/rfqs');
      setRfqs(res.data);
    } catch (err) {
      console.error('Failed to load RFQs', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRfqs();

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
            fetchRfqs();
          }
        } catch (e) {
          // ignore
        }
      };
    } catch (e) {
      // ignore
    }

    // 2. Poll every 5s and re-fetch on window focus
    const interval = setInterval(fetchRfqs, 5000);
    window.addEventListener('focus', fetchRfqs);

    return () => {
      if (socket) socket.close();
      clearInterval(interval);
      window.removeEventListener('focus', fetchRfqs);
    };
  }, []);

  const filtered = rfqs.filter((r) => {
    const rStatus = (r.status || '').toUpperCase();
    if (statusFilter === 'ACTIVE' && rStatus !== 'ACTIVE') return false;
    if (statusFilter === 'SCHEDULED' && rStatus !== 'SCHEDULED') return false;
    if (statusFilter === 'CLOSED' && rStatus !== 'CLOSED' && rStatus !== 'FORCE_CLOSED') return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        (r.name || '').toLowerCase().includes(q) ||
        (r.reference_id || '').toLowerCase().includes(q) ||
        (r.origin || '').toLowerCase().includes(q) ||
        (r.destination || '').toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#111111]">RFQs</h1>
          <p className="text-sm font-normal text-[#777777] mt-1">
            Manage procurement requests, schedules and auction settings.
          </p>
        </div>

        <button
          onClick={() => navigate('/rfqs/new')}
          className="h-9 px-4 bg-[#111111] hover:bg-black text-white text-sm font-medium rounded-[4px] flex items-center gap-2 cursor-pointer transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create RFQ</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-[#E5E5E5] pb-4">
        <div className="flex items-center gap-2 text-xs font-medium">
          {['ALL', 'ACTIVE', 'SCHEDULED', 'CLOSED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-[4px] border cursor-pointer transition-colors ${
                statusFilter === st
                  ? 'bg-[#111111] text-white border-[#111111]'
                  : 'bg-white text-[#777777] border-[#E5E5E5] hover:text-[#111111]'
              }`}
            >
              {st === 'ALL' ? 'All' : st}
            </button>
          ))}
        </div>

        <div className="relative min-w-[260px]">
          <input
            type="text"
            placeholder="Search by ID, name, port..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-3 pr-3 py-1.5 text-xs bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
          />
        </div>
      </div>

      {/* Table */}
      <div className="border border-[#E5E5E5] rounded-[4px] overflow-hidden bg-white">
        {isLoading ? (
          <div className="py-8 text-center text-xs text-[#777777]">Loading RFQs...</div>
        ) : filtered.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#777777]">No RFQs found.</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-[#FAFAFA] border-b border-[#E5E5E5] text-[#777777] text-xs font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4 font-semibold">RFQ ID</th>
                <th className="py-2.5 px-4 font-semibold">RFQ Name</th>
                <th className="py-2.5 px-4 font-semibold">Route</th>
                <th className="py-2.5 px-4 font-semibold">Pickup Date</th>
                <th className="py-2.5 px-4 font-semibold">Lowest Bid</th>
                <th className="py-2.5 px-4 font-semibold">Closing Time</th>
                <th className="py-2.5 px-4 font-semibold">Status</th>
                <th className="py-2.5 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E5E5]">
              {filtered.map((rfq) => (
                <tr key={rfq.id} className="hover:bg-[#FAFAFA] transition-colors">
                  <td className="py-3 px-4 font-mono text-xs font-medium text-[#111111]">
                    {rfq.reference_id}
                  </td>
                  <td className="py-3 px-4 font-medium text-[#111111]">
                    {rfq.name}
                  </td>
                  <td className="py-3 px-4 text-xs text-[#777777]">
                    {rfq.origin} → {rfq.destination}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-[#777777]">
                    {new Date(rfq.pickup_service_date).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 font-mono text-sm font-medium text-[#111111]">
                    {rfq.current_lowest_bid ? `$${rfq.current_lowest_bid.toLocaleString()}` : <span className="text-[#777777]">—</span>}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-[#777777]">
                    {new Date(rfq.current_bid_close_time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
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
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
