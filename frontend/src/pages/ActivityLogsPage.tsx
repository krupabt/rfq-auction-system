import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Search } from 'lucide-react';

export const ActivityLogsPage: React.FC = () => {
  const [activities, setActivities] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await api.get('/dashboard/recent-activities');
        setActivities(res.data);
      } catch (err) {
        console.error('Failed to load activities', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const filtered = activities.filter((act) => {
    if (eventTypeFilter !== 'ALL' && act.event_type !== eventTypeFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        act.description.toLowerCase().includes(q) ||
        (act.rfq_ref && act.rfq_ref.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[#E5E5E5]">
        <h1 className="text-[24px] font-semibold text-[#111111]">
          Activity Logs
        </h1>
        <p className="text-[14px] text-[#777777]">
          Audit trail of RFQ creations, quote submissions, time extensions, and status changes.
        </p>
      </div>

      {/* Filter and Search */}
      <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {['ALL', 'BID_SUBMITTED', 'AUCTION_EXTENDED', 'RFQ_CREATED'].map((t) => (
            <button
              key={t}
              onClick={() => setEventTypeFilter(t)}
              className={`px-3 py-1.5 rounded-[4px] text-[14px] font-medium transition-colors ${
                eventTypeFilter === t
                  ? 'bg-[#111111] text-white'
                  : 'bg-white text-[#111111] border border-[#E5E5E5] hover:bg-[#F9F9F9]'
              }`}
            >
              {t === 'ALL' ? 'All Events' : t.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-[#777777] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search activity description, RFQ ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
          />
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-[#E5E5E5] rounded-[4px] overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-[14px] text-[#777777]">Loading activity logs...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-[14px] text-[#777777]">No activity logs found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E5E5E5] bg-[#FAFAFA]">
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Event</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">RFQ Ref</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Description</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5]">
                {filtered.map((act) => (
                  <tr key={act.id} className="hover:bg-[#F9F9F9] transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-mono text-[12px] font-medium text-[#111111] border border-[#E5E5E5] px-2 py-0.5 rounded-[4px]">
                        {act.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[14px] text-[#111111]">
                      {act.rfq_ref || '—'}
                    </td>
                    <td className="py-3 px-4 text-[14px] text-[#111111]">
                      {act.description}
                    </td>
                    <td className="py-3 px-4 font-mono text-[12px] text-[#777777] text-right">
                      {new Date(act.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
