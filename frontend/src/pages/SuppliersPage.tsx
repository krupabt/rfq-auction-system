import React, { useState, useEffect } from 'react';
import api from '../services/api';

export const SuppliersPage: React.FC = () => {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSuppliers = async () => {
      try {
        const res = await api.get('/reports/supplier-performance');
        setSuppliers(res.data);
      } catch (err) {
        console.error('Failed to load suppliers', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSuppliers();
  }, []);

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[#E5E5E5]">
        <h1 className="text-[24px] font-semibold text-[#111111]">
          Suppliers
        </h1>
        <p className="text-[14px] text-[#777777]">
          Directory of registered carrier partners, quote history and auction win rates.
        </p>
      </div>

      <div className="bg-white border border-[#E5E5E5] rounded-[4px] overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-[14px] text-[#777777]">Loading suppliers...</div>
        ) : suppliers.length === 0 ? (
          <div className="p-8 text-center text-[14px] text-[#777777]">No registered suppliers found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E5E5E5] bg-[#FAFAFA]">
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Carrier / Supplier</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Contact Person</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Auctions</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Quotes Placed</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">L1 Wins</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase">Win Rate</th>
                  <th className="py-2.5 px-4 text-[12px] font-semibold text-[#777777] uppercase text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E5]">
                {suppliers.map((s) => (
                  <tr key={s.supplier_id} className="hover:bg-[#F9F9F9] transition-colors">
                    <td className="py-3 px-4 text-[14px] font-medium text-[#111111]">
                      {s.company_name}
                    </td>
                    <td className="py-3 px-4 text-[14px] text-[#777777]">
                      {s.contact_person || '—'}
                    </td>
                    <td className="py-3 px-4 text-[14px] font-mono text-[#111111]">
                      {s.total_auctions_participated}
                    </td>
                    <td className="py-3 px-4 text-[14px] font-mono text-[#111111]">
                      {s.total_bids_placed}
                    </td>
                    <td className="py-3 px-4 text-[14px] font-mono text-[#111111]">
                      {s.auctions_won}
                    </td>
                    <td className="py-3 px-4 text-[14px] font-mono text-[#111111]">
                      {s.win_rate_percentage}%
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="inline-block px-2 py-0.5 text-[12px] font-medium text-[#1E7E34] bg-[#EBF7EE] border border-[#C3E6CB] rounded-[4px]">
                        Verified
                      </span>
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
