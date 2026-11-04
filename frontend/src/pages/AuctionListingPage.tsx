import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { Search } from 'lucide-react';

interface AuctionListingPageProps {
  activeOnly?: boolean;
}

export const AuctionListingPage: React.FC<AuctionListingPageProps> = ({ activeOnly = false }) => {
  const navigate = useNavigate();
  const [auctions, setAuctions] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState(activeOnly ? 'ACTIVE' : 'ALL');
  const [sortBy, setSortBy] = useState('closing_time');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const [isLoading, setIsLoading] = useState(true);

  const fetchAuctions = async () => {
    try {
      const queryParams = new URLSearchParams();
      if (activeOnly) {
        queryParams.append('status_filter', 'ACTIVE');
      } else if (statusFilter !== 'ALL') {
        queryParams.append('status_filter', statusFilter);
      }
      queryParams.append('sort_by', sortBy);

      const res = await api.get(`/auctions?${queryParams.toString()}`);
      setAuctions(res.data);
    } catch (err) {
      console.error('Failed to load auctions', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuctions();

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
            fetchAuctions();
          }
        } catch (e) {
          // ignore
        }
      };
    } catch (e) {
      // ignore
    }

    // 2. Poll every 5s and re-fetch on window focus
    const interval = setInterval(fetchAuctions, 5000);
    window.addEventListener('focus', fetchAuctions);

    return () => {
      if (socket) socket.close();
      clearInterval(interval);
      window.removeEventListener('focus', fetchAuctions);
    };
  }, [activeOnly, statusFilter, sortBy]);

  const filtered = auctions.filter((a) => {
    if (search) {
      const q = search.toLowerCase();
      return (
        a.name.toLowerCase().includes(q) ||
        a.reference_id.toLowerCase().includes(q) ||
        a.origin.toLowerCase().includes(q) ||
        a.destination.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalPages = Math.ceil(filtered.length / itemsPerPage) || 1;
  const paginated = filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E5E5]">
        <div>
          <h1 className="text-[24px] font-semibold text-[#111111]">
            {activeOnly ? 'Active Auctions' : 'Auctions'}
          </h1>
          <p className="text-[14px] text-[#777777]">
            Monitor British reverse auctions, live supplier bidding, and closing times.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px] flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Status Filters */}
        {!activeOnly && (
          <div className="flex items-center gap-1.5 overflow-x-auto">
            {['ALL', 'ACTIVE', 'SCHEDULED', 'CLOSED'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  setCurrentPage(1);
                }}
                className={`px-3 py-1.5 rounded-[4px] text-[14px] font-medium transition-colors ${
                  statusFilter === st
                    ? 'bg-[#111111] text-white'
                    : 'bg-white text-[#111111] border border-[#E5E5E5] hover:bg-[#F9F9F9]'
                }`}
              >
                {st === 'ALL' ? 'All Auctions' : st}
              </button>
            ))}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Sort By Dropdown */}
          <div className="flex items-center gap-2 text-[14px] text-[#777777]">
            <span>Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-2.5 py-1.5 bg-white border border-[#E5E5E5] rounded-[4px] text-[14px] text-[#111111] focus:outline-none focus:border-[#111111]"
            >
              <option value="closing_time">Closing Soonest</option>
              <option value="lowest_bid">Lowest Bid (L1)</option>
              <option value="created_at">Recently Created</option>
            </select>
          </div>

          {/* Search Box */}
          <div className="relative min-w-[240px]">
            <Search className="w-4 h-4 text-[#777777] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search RFQ name, ID, route..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
            />
          </div>
        </div>
      </div>

      {/* Auctions Table */}
      <div className="bg-white border border-[#E5E5E5] rounded-[4px] overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-[14px] text-[#777777]">Loading auctions...</div>
        ) : paginated.length === 0 ? (
          <div className="p-8 text-center text-[14px] text-[#777777]">No auctions found matching criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E5E5E5] bg-[#FAFAFA]">
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">RFQ ID</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">RFQ Name</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Route</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Lowest Bid (L1)</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Bids</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Closing Time</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Status</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5]">
                {paginated.map((auc) => (
                  <tr key={auc.id} className="hover:bg-[#F9F9F9] transition-colors">
                    <td className="py-3 px-4 text-[14px] font-mono text-[#111111]">
                      {auc.reference_id}
                    </td>
                    <td className="py-3 px-4 text-[14px] font-medium text-[#111111]">
                      {auc.name}
                    </td>
                    <td className="py-3 px-4 text-[14px] text-[#777777]">
                      {auc.origin} → {auc.destination}
                    </td>
                    <td className="py-3 px-4 text-[14px] font-medium text-[#111111]">
                      {auc.current_lowest_bid != null ? `$${auc.current_lowest_bid.toLocaleString()}` : '—'}
                    </td>
                    <td className="py-3 px-4 text-[14px] text-[#777777]">
                      {auc.total_bids_count}
                    </td>
                    <td className="py-3 px-4 text-[14px] text-[#777777]">
                      {new Date(auc.current_bid_close_time).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={auc.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => navigate(`/auctions/${auc.id}`)}
                        className="px-3 py-1 bg-[#111111] hover:bg-black text-white rounded-[4px] text-[14px] font-medium transition-colors"
                      >
                        View Auction
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-3 border-t border-[#E5E5E5] flex items-center justify-between text-[14px] text-[#777777]">
            <span>
              Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
              {Math.min(currentPage * itemsPerPage, filtered.length)} of {filtered.length} auctions
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-[#E5E5E5] rounded-[4px] text-[#111111] disabled:text-[#CCCCCC] hover:bg-[#F9F9F9]"
              >
                Previous
              </button>
              <span className="px-2 text-[14px] text-[#111111]">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-[#E5E5E5] rounded-[4px] text-[#111111] disabled:text-[#CCCCCC] hover:bg-[#F9F9F9]"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
