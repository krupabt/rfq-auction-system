import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { StatusBadge } from '../components/StatusBadge';

export const ReportsPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get('/reports/analytics');
        setData(res.data);
      } catch (err) {
        console.error('Failed to load reports', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (isLoading || !data) {
    return <div className="p-8 text-center text-[14px] text-[#777777]">Loading procurement reports...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[#E5E5E5]">
        <h1 className="text-[24px] font-semibold text-[#111111]">
          Reports & Analytics
        </h1>
        <p className="text-[14px] text-[#777777]">
          Procurement metrics, British Auction extension frequency, and realized cost savings.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px]">
          <span className="text-[12px] font-medium uppercase text-[#777777] block">Total Auctions</span>
          <span className="font-mono text-[20px] font-semibold text-[#111111] mt-1 block">
            {data.total_auctions}
          </span>
          <span className="text-[12px] text-[#777777]">All created events</span>
        </div>

        <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px]">
          <span className="text-[12px] font-medium uppercase text-[#777777] block">Completed</span>
          <span className="font-mono text-[20px] font-semibold text-[#111111] mt-1 block">
            {data.completed_auctions}
          </span>
          <span className="text-[12px] text-[#777777]">Finalized events</span>
        </div>

        <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px]">
          <span className="text-[12px] font-medium uppercase text-[#777777] block">Total Quotes</span>
          <span className="font-mono text-[20px] font-semibold text-[#111111] mt-1 block">
            {data.total_bids}
          </span>
          <span className="text-[12px] text-[#777777]">Across all suppliers</span>
        </div>

        <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px]">
          <span className="text-[12px] font-medium uppercase text-[#777777] block">Avg Quotes / RFQ</span>
          <span className="font-mono text-[20px] font-semibold text-[#111111] mt-1 block">
            {data.average_bids_per_auction}
          </span>
          <span className="text-[12px] text-[#777777]">Competition density</span>
        </div>

        <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px]">
          <span className="text-[12px] font-medium uppercase text-[#777777] block">Avg Extensions</span>
          <span className="font-mono text-[20px] font-semibold text-[#111111] mt-1 block">
            {data.average_extensions_per_auction}
          </span>
          <span className="text-[12px] text-[#777777]">Per British auction</span>
        </div>

        <div className="bg-white p-4 border border-[#E5E5E5] rounded-[4px]">
          <span className="text-[12px] font-medium uppercase text-[#777777] block">Total Savings</span>
          <span className="font-mono text-[20px] font-semibold text-[#111111] mt-1 block">
            ${data.total_savings_generated?.toLocaleString()}
          </span>
          <span className="text-[12px] text-[#777777]">Below target baseline</span>
        </div>
      </div>

      {/* Distribution Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-5 border border-[#E5E5E5] rounded-[4px] space-y-3">
          <h2 className="text-[16px] font-semibold text-[#111111]">
            Status Distribution
          </h2>

          <div className="space-y-2.5">
            {Object.entries(data.status_distribution || {}).map(([st, cnt]: [string, any]) => {
              const total = data.total_auctions || 1;
              const pct = Math.round((cnt / total) * 100);
              return (
                <div key={st} className="space-y-1">
                  <div className="flex justify-between text-[14px]">
                    <span className="text-[#111111]">{st}</span>
                    <span className="font-mono text-[#777777]">{cnt} ({pct}%)</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#F2F2F2] rounded-[2px] overflow-hidden">
                    <div
                      className="h-full bg-[#111111]"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white p-5 border border-[#E5E5E5] rounded-[4px] space-y-3">
          <h2 className="text-[16px] font-semibold text-[#111111]">
            British Auction Trigger Rule Adoption
          </h2>

          <div className="space-y-2.5">
            {Object.entries(data.trigger_type_distribution || {}).map(([tt, cnt]: [string, any]) => {
              const total = data.total_auctions || 1;
              const pct = Math.round((cnt / total) * 100);
              return (
                <div key={tt} className="space-y-1">
                  <div className="flex justify-between text-[14px]">
                    <span className="font-mono text-[#111111]">{tt}</span>
                    <span className="font-mono text-[#777777]">{cnt} ({pct}%)</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#F2F2F2] rounded-[2px] overflow-hidden">
                    <div
                      className="h-full bg-[#111111]"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Historical Auction Results Table */}
      <div className="bg-white border border-[#E5E5E5] rounded-[4px] overflow-hidden">
        <div className="p-4 border-b border-[#E5E5E5]">
          <h2 className="text-[16px] font-semibold text-[#111111]">
            Historical Auction Results & Contract Allocation
          </h2>
          <p className="text-[12px] text-[#777777]">
            Final lowest quotes, winning carriers, and realized cost savings.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E5E5] bg-[#FAFAFA]">
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">RFQ ID</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">RFQ Name</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Status</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Winning L1 Supplier</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Final Lowest Quote</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Target Rate</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Cost Savings</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Quotes</th>
                <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Extensions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E5E5]">
              {data.auction_summaries.map((s: any) => (
                <tr key={s.rfq_id} className="hover:bg-[#F9F9F9] transition-colors">
                  <td className="py-3 px-4 font-mono text-[14px] text-[#111111]">{s.reference_id}</td>
                  <td className="py-3 px-4 text-[14px] font-medium text-[#111111]">{s.name}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="py-3 px-4 text-[14px] text-[#111111]">
                    {s.winning_supplier || <span className="text-[#777777] italic">No award</span>}
                  </td>
                  <td className="py-3 px-4 font-mono text-[14px] font-medium text-[#111111]">
                    {s.final_lowest_quote ? `$${s.final_lowest_quote.toLocaleString()}` : '—'}
                  </td>
                  <td className="py-3 px-4 font-mono text-[14px] text-[#777777]">
                    {s.target_price ? `$${s.target_price.toLocaleString()}` : '—'}
                  </td>
                  <td className="py-3 px-4 text-[14px] font-mono text-[#111111]">
                    {s.savings_amount ? `$${s.savings_amount.toLocaleString()} (${s.savings_percentage}%)` : '—'}
                  </td>
                  <td className="py-3 px-4 font-mono text-[14px] text-[#777777]">{s.total_bids}</td>
                  <td className="py-3 px-4 font-mono text-[14px] text-[#111111]">{s.total_extensions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
