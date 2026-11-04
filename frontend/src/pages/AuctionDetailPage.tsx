import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/StatusBadge';
import { CountdownTimer } from '../components/CountdownTimer';
import { TriggerRuleBadge } from '../components/TriggerRuleBadge';
import { ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react';

export const AuctionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [auction, setAuction] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Quote form state
  const [carrierName, setCarrierName] = useState(
    user?.supplier_profile?.company_name || ''
  );
  const [freightCharges, setFreightCharges] = useState<number | ''>('');
  const [originCharges, setOriginCharges] = useState<number | ''>('');
  const [destinationCharges, setDestinationCharges] = useState<number | ''>('');
  const [transitTime, setTransitTime] = useState<number | ''>('');
  const [validityDays, setValidityDays] = useState<number>(30);
  const [notes, setNotes] = useState('');

  // Keep carrier name synced with current authenticated supplier account
  useEffect(() => {
    if (user?.supplier_profile?.company_name) {
      setCarrierName(user.supplier_profile.company_name);
    }
  }, [user]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);

  // Demo simulator state
  const [isDemoAdjusting, setIsDemoAdjusting] = useState(false);

  // Auto total calculation
  const totalQuoteInForm =
    (Number(freightCharges) || 0) +
    (Number(originCharges) || 0) +
    (Number(destinationCharges) || 0);

  const formatTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? '—' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Fetch auction details
  const fetchDetails = async () => {
    try {
      const res = await api.get(`/auctions/${id}`);
      setAuction(res.data);
      if (!carrierName && user?.supplier_profile?.company_name) {
        setCarrierName(user.supplier_profile.company_name);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load auction.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id]);

  // WebSocket Live Updates
  useEffect(() => {
    if (!id) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/auctions/${id}`;

    let socket: WebSocket;
    try {
      socket = new WebSocket(wsUrl);

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'BID_SUBMITTED' || payload.type === 'AUCTION_EXTENDED') {
            if (payload.data?.new_close_time) {
              setAuction((prev: any) => prev ? {
                ...prev,
                current_bid_close_time: payload.data.new_close_time,
                extension_count: payload.data.was_extended ? (prev.extension_count || 0) + 1 : prev.extension_count
              } : prev);
            }
            fetchDetails();
          }
        } catch (e) {
          // heartbeat
        }
      };
    } catch (e) {
      console.error('WebSocket connection failed', e);
    }

    return () => {
      if (socket) socket.close();
    };
  }, [id]);

  const handleSubmitQuote = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);

    if (!carrierName.trim()) {
      setSubmitError('Carrier name is required.');
      return;
    }
    if (freightCharges === '' || Number(freightCharges) <= 0) {
      setSubmitError('Freight charges must be greater than zero.');
      return;
    }
    if (transitTime === '' || Number(transitTime) <= 0) {
      setSubmitError('Transit time must be greater than zero.');
      return;
    }

    setIsSubmitting(true);
    try {
      const validityDate = new Date();
      validityDate.setDate(validityDate.getDate() + (Number(validityDays) || 30));

      const payload = {
        carrier_name: carrierName.trim(),
        freight_charges: Number(freightCharges),
        origin_charges: Number(originCharges) || 0,
        destination_charges: Number(destinationCharges) || 0,
        transit_time: Number(transitTime),
        validity_of_quote: validityDate.toISOString(),
        notes: notes.trim() || undefined,
      };

      const res = await api.post(`/auctions/${id}/bids`, payload);
      setSubmitSuccess(`Quote of $${res.data.total_quote.toLocaleString()} placed successfully (Rank L${res.data.rank_at_submission}).`);

      // Clear input fields
      setFreightCharges('');
      setOriginCharges('');
      setDestinationCharges('');
      setNotes('');

      fetchDetails();
    } catch (err: any) {
      setSubmitError(err.response?.data?.detail || 'Failed to submit quote.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoTimeAdjust = async (minutes: number) => {
    setIsDemoAdjusting(true);
    try {
      await api.post(`/auctions/${id}/demo-time?remaining_minutes=${minutes}`);
      fetchDetails();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Demo adjustment failed');
    } finally {
      setIsDemoAdjusting(false);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center text-[14px] text-[#777777]">Loading auction details...</div>;
  }

  if (error || !auction) {
    return (
      <div className="p-4 bg-white border border-red-300 rounded-[4px] text-[14px] text-red-700">
        {error || 'Auction not found'}
      </div>
    );
  }

  const isBiddingClosed = auction.status === 'CLOSED' || auction.status === 'FORCE_CLOSED';

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#E5E5E5]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/auctions')}
            className="p-1.5 border border-[#E5E5E5] rounded-[4px] text-[#111111] hover:bg-[#F9F9F9]"
            title="Back to Auctions"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[12px] font-semibold text-[#111111] border border-[#E5E5E5] px-2 py-0.5 rounded-[4px]">
                {auction.reference_id}
              </span>
              <StatusBadge status={auction.status} />
              {auction.extension_count > 0 && (
                <span className="text-[12px] font-medium text-[#777777] border border-[#E5E5E5] px-2 py-0.5 rounded-[4px]">
                  Extended {auction.extension_count} time{auction.extension_count > 1 ? 's' : ''}
                </span>
              )}
            </div>
            <h1 className="text-[24px] font-semibold text-[#111111] mt-1">
              {auction.name}
            </h1>
          </div>
        </div>

        {/* Evaluator Fast-Forward Simulator Toolbar */}
        <div className="flex items-center gap-2">
          <span className="text-[12px] text-[#777777]">Evaluator Fast-Forward:</span>
          <button
            onClick={() => handleDemoTimeAdjust(auction.auction_config ? auction.auction_config.trigger_window_minutes - 1 : 9)}
            disabled={isDemoAdjusting || isBiddingClosed}
            className="px-2.5 py-1 bg-white hover:bg-[#F9F9F9] text-[#111111] border border-[#111111] rounded-[4px] text-[12px] font-medium disabled:border-[#E5E5E5] disabled:text-[#AAAAAA]"
            title="Jump to within trigger window to observe extension"
          >
            Trigger Window ({auction.auction_config?.trigger_window_minutes - 1 || 9}m left)
          </button>
          <button
            onClick={() => handleDemoTimeAdjust(0.5)}
            disabled={isDemoAdjusting || isBiddingClosed}
            className="px-2.5 py-1 bg-white hover:bg-[#F9F9F9] text-[#111111] border border-[#111111] rounded-[4px] text-[12px] font-medium disabled:border-[#E5E5E5] disabled:text-[#AAAAAA]"
            title="Jump to final 30 seconds"
          >
            30s Crunch
          </button>
        </div>
      </div>

      {/* Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Clock, Rules, Bidding Form */}
        <div className="lg:col-span-5 space-y-6">
          {/* Live Countdown Clock */}
          <CountdownTimer
            closeTime={auction.current_bid_close_time}
            forcedCloseTime={auction.forced_bid_close_time}
            triggerWindowMinutes={auction.auction_config?.trigger_window_minutes ?? 10}
            status={auction.status}
            onExpire={fetchDetails}
          />

          {/* British Auction Configuration Display */}
          <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-5 space-y-3">
            <h2 className="text-[16px] font-semibold text-[#111111]">
              Auction Configuration & Rules
            </h2>

            <div className="grid grid-cols-2 gap-3 text-[14px]">
              <div className="p-3 bg-[#FAFAFA] border border-[#E5E5E5] rounded-[4px]">
                <span className="text-[12px] text-[#777777] block uppercase font-medium">Trigger Window (X)</span>
                <span className="text-[16px] font-semibold text-[#111111] mt-0.5 block font-mono">
                  {auction.auction_config?.trigger_window_minutes ?? 10} Minutes
                </span>
                <span className="text-[12px] text-[#777777]">Monitors activity near close</span>
              </div>

              <div className="p-3 bg-[#FAFAFA] border border-[#E5E5E5] rounded-[4px]">
                <span className="text-[12px] text-[#777777] block uppercase font-medium">Extension Duration (Y)</span>
                <span className="text-[16px] font-semibold text-[#111111] mt-0.5 block font-mono">
                  +{auction.auction_config?.extension_duration_minutes ?? 5} Minutes
                </span>
                <span className="text-[12px] text-[#777777]">Added per trigger event</span>
              </div>
            </div>

            <div className="p-3 border border-[#E5E5E5] rounded-[4px] space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[14px] font-medium text-[#111111]">Extension Condition:</span>
                <TriggerRuleBadge type={auction.auction_config?.extension_trigger_type || 'L1_RANK_CHANGE'} />
              </div>
              <p className="text-[12px] text-[#777777] leading-relaxed pt-1">
                {auction.auction_config?.extension_trigger_type === 'ANY_BID' && 'Any quote placed during the trigger window extends the auction by Y minutes.'}
                {auction.auction_config?.extension_trigger_type === 'ANY_RANK_CHANGE' && 'Any quote that changes supplier ranks during the trigger window extends the auction.'}
                {auction.auction_config?.extension_trigger_type === 'L1_RANK_CHANGE' && 'Auction extends only when the leading lowest-priced quote (L1) is beaten.'}
              </p>
            </div>

            {/* Timing Milestones */}
            <div className="pt-2 border-t border-[#E5E5E5] space-y-1 text-[12px] text-[#777777]">
              <div className="flex justify-between">
                <span>Original Scheduled Close:</span>
                <span className="font-mono text-[#111111]">
                  {new Date(auction.original_bid_close_time).toLocaleTimeString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Current Effective Close:</span>
                <span className="font-mono font-semibold text-[#111111]">
                  {new Date(auction.current_bid_close_time).toLocaleTimeString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Hard Forced Close Limit:</span>
                <span className="font-mono font-semibold text-[#111111]">
                  {new Date(auction.forced_bid_close_time).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>

          {/* Supplier Quote Submission Form */}
          <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-[16px] font-semibold text-[#111111]">
                Submit Quote
              </h2>
              {auction.current_lowest_bid && (
                <span className="text-[12px] text-[#777777]">
                  L1 to beat: <strong className="font-mono text-[#111111]">&lt; ${auction.current_lowest_bid.toLocaleString()}</strong>
                </span>
              )}
            </div>

            {/* Authenticated Supplier Account Status */}
            <div className="p-2.5 bg-[#FAFAFA] border border-[#E5E5E5] rounded-[4px] text-[12px] flex items-center justify-between">
              <span className="text-[#777777]">Authenticated Supplier:</span>
              <span className="font-semibold text-[#111111]">
                {user?.supplier_profile?.company_name || user?.full_name || 'Anonymous'}
              </span>
            </div>

            {/* Quick Pricing Presets */}
            <div>
              <span className="text-[12px] text-[#777777] block mb-1">
                Quick Competitive Quotes:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { label: 'Beat L1 (-$50)', delta: -50 },
                  { label: 'Beat L1 (-$150)', delta: -150 },
                  { label: 'Beat L1 (-$300)', delta: -300 },
                ].map((p) => {
                  const targetTotal = (auction.current_lowest_bid || 2500) + p.delta;
                  const calculatedFreight = Math.max(200, targetTotal - 350);
                  return (
                    <button
                      key={p.label}
                      type="button"
                      onClick={() => {
                        if (!carrierName && user?.supplier_profile?.company_name) {
                          setCarrierName(user.supplier_profile.company_name);
                        }
                        setFreightCharges(calculatedFreight);
                        setOriginCharges(200);
                        setDestinationCharges(150);
                        setTransitTime(15);
                        setSubmitError(null);
                      }}
                      className="text-[12px] px-2.5 py-1 bg-white hover:bg-[#F9F9F9] text-[#111111] border border-[#E5E5E5] rounded-[4px]"
                    >
                      {p.label} (${targetTotal.toLocaleString()})
                    </button>
                  );
                })}
              </div>
            </div>

            <form onSubmit={handleSubmitQuote} className="space-y-3">
              <div>
                <label className="block text-[14px] font-medium text-[#111111] mb-1">
                  Operating Carrier / Fleet Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. A.P. Moller - Maersk or MSC Line"
                  value={carrierName}
                  onChange={(e) => setCarrierName(e.target.value)}
                  disabled={isBiddingClosed || isSubmitting}
                  className="w-full px-3 py-1.5 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  required
                />
                <span className="text-[11px] text-[#777777] mt-0.5 block">
                  Quote is linked to supplier account: <strong>{user?.supplier_profile?.company_name || user?.full_name}</strong>
                </span>
              </div>

              {/* Charge Breakdown */}
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[12px] font-medium text-[#111111] mb-1">Freight ($) *</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="2000"
                    value={freightCharges}
                    onChange={(e) => setFreightCharges(e.target.value === '' ? '' : Number(e.target.value))}
                    disabled={isBiddingClosed || isSubmitting}
                    className="w-full px-2.5 py-1.5 text-[14px] text-[#111111] font-mono bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-[#111111] mb-1">Origin ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="200"
                    value={originCharges}
                    onChange={(e) => setOriginCharges(e.target.value === '' ? '' : Number(e.target.value))}
                    disabled={isBiddingClosed || isSubmitting}
                    className="w-full px-2.5 py-1.5 text-[14px] text-[#111111] font-mono bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-[#111111] mb-1">Dest ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="150"
                    value={destinationCharges}
                    onChange={(e) => setDestinationCharges(e.target.value === '' ? '' : Number(e.target.value))}
                    disabled={isBiddingClosed || isSubmitting}
                    className="w-full px-2.5 py-1.5 text-[14px] text-[#111111] font-mono bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  />
                </div>
              </div>

              {/* Total Quote Display */}
              <div className="p-2.5 bg-[#FAFAFA] border border-[#E5E5E5] rounded-[4px] flex items-center justify-between text-[14px]">
                <span className="text-[#777777]">Calculated Total Quote:</span>
                <span className="font-mono text-[16px] font-semibold text-[#111111]">
                  ${totalQuoteInForm.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[14px]">
                <div>
                  <label className="block text-[12px] font-medium text-[#111111] mb-1">Transit Time (Days) *</label>
                  <input
                    type="number"
                    min="1"
                    placeholder="e.g. 15"
                    value={transitTime}
                    onChange={(e) => setTransitTime(e.target.value === '' ? '' : Number(e.target.value))}
                    disabled={isBiddingClosed || isSubmitting}
                    className="w-full px-2.5 py-1.5 text-[14px] text-[#111111] font-mono bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-[#111111] mb-1">Validity (Days)</label>
                  <input
                    type="number"
                    min="1"
                    value={validityDays}
                    onChange={(e) => setValidityDays(Number(e.target.value))}
                    disabled={isBiddingClosed || isSubmitting}
                    className="w-full px-2.5 py-1.5 text-[14px] text-[#111111] font-mono bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[12px] font-medium text-[#111111] mb-1">Notes / Terms</label>
                <input
                  type="text"
                  placeholder="e.g. 14 days free demurrage included"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  disabled={isBiddingClosed || isSubmitting}
                  className="w-full px-3 py-1.5 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                />
              </div>

              {submitError && (
                <div className="p-2.5 bg-white border border-red-300 rounded-[4px] text-[12px] text-red-700 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{submitError}</span>
                </div>
              )}

              {submitSuccess && (
                <div className="p-2.5 bg-white border border-[#111111] rounded-[4px] text-[12px] text-[#111111] flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{submitSuccess}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isBiddingClosed || isSubmitting}
                className="w-full py-2 bg-[#111111] hover:bg-black disabled:bg-[#CCCCCC] text-white rounded-[4px] text-[14px] font-medium transition-colors"
              >
                {isBiddingClosed
                  ? 'Bidding Closed'
                  : isSubmitting
                  ? 'Submitting Quote...'
                  : 'Submit Quote'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column (7 cols): Leaderboard, Quotes History, Activity Timeline */}
        <div className="lg:col-span-7 space-y-6">
          {/* Supplier Ranking Leaderboard */}
          <div className="bg-white border border-[#E5E5E5] rounded-[4px] overflow-hidden">
            <div className="p-4 border-b border-[#E5E5E5] flex items-center justify-between">
              <div>
                <h2 className="text-[16px] font-semibold text-[#111111]">
                  Supplier Rankings
                </h2>
                <p className="text-[12px] text-[#777777]">
                  Ranked by lowest total quote. Earlier submission breaks ties.
                </p>
              </div>
              <span className="text-[12px] text-[#777777] border border-[#E5E5E5] px-2 py-0.5 rounded-[4px]">
                {auction.rankings?.length ?? 0} Supplier{auction.rankings?.length === 1 ? '' : 's'}
              </span>
            </div>

            {!auction.rankings || auction.rankings.length === 0 ? (
              <div className="text-center py-8 text-[14px] text-[#777777]">
                No quotes placed yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[#E5E5E5] bg-[#FAFAFA]">
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Rank</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Supplier Account</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Operating Carrier</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Freight</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Origin / Dest</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Total Quote</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Transit</th>
                      <th className="py-2.5 px-3 text-[12px] font-semibold text-[#777777] uppercase">Submitted</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E5E5]">
                    {auction.rankings.map((r: any) => {
                      const isL1 = r.rank === 1;
                      const isL2 = r.rank === 2;
                      const isL3 = r.rank === 3;
                      return (
                        <tr
                          key={r.supplier_id}
                          className={`hover:bg-[#F9F9F9] transition-colors ${
                            isL1 ? 'bg-[#FAFAFA]' : ''
                          }`}
                        >
                          <td className="py-3 px-3">
                            <span
                              className={`inline-block px-2 py-0.5 text-[12px] font-semibold rounded-[4px] ${
                                isL1
                                  ? 'bg-[#EBF7EE] text-[#1E7E34] border border-[#C3E6CB]'
                                  : isL2 || isL3
                                  ? 'bg-[#F2F2F2] text-[#111111] border border-[#E5E5E5]'
                                  : 'text-[#777777]'
                              }`}
                            >
                              L{r.rank}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <div className="text-[14px] font-medium text-[#111111]">{r.supplier_name || r.company_name || '—'}</div>
                            <div className="text-[11px] text-[#777777]">ID #{r.supplier_id}</div>
                          </td>
                          <td className="py-3 px-3 text-[13px] text-[#111111]">
                            {r.carrier_name}
                          </td>
                          <td className="py-3 px-3 text-[14px] font-mono text-[#111111]">
                            ${r.freight_charges?.toLocaleString()}
                          </td>
                          <td className="py-3 px-3 text-[12px] text-[#777777]">
                            ${r.origin_charges} / ${r.destination_charges}
                          </td>
                          <td className="py-3 px-3 text-[14px] font-mono font-semibold text-[#111111]">
                            ${r.total_quote?.toLocaleString()}
                          </td>
                          <td className="py-3 px-3 text-[14px] text-[#777777]">
                            {r.transit_time} days
                          </td>
                          <td className="py-3 px-3 text-[12px] text-[#777777]">
                            {formatTime(r.last_bid_time || r.last_bid_at)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Quotes Audit History */}
          <div className="bg-white border border-[#E5E5E5] rounded-[4px] overflow-hidden">
            <div className="p-4 border-b border-[#E5E5E5] flex items-center justify-between">
              <div>
                <h2 className="text-[16px] font-semibold text-[#111111]">
                  Quote History
                </h2>
                <p className="text-[12px] text-[#777777]">
                  All submitted quotes in chronological sequence.
                </p>
              </div>
              <span className="text-[12px] text-[#777777] border border-[#E5E5E5] px-2 py-0.5 rounded-[4px]">
                {auction.bids?.length ?? 0} Quotes
              </span>
            </div>

            {!auction.bids || auction.bids.length === 0 ? (
              <div className="text-center py-6 text-[14px] text-[#777777]">
                No quotes submitted.
              </div>
            ) : (
              <div className="overflow-x-auto max-h-[280px]">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[#E5E5E5] bg-[#FAFAFA] sticky top-0">
                      <th className="py-2 px-3 text-[12px] font-semibold text-[#777777] uppercase">Time</th>
                      <th className="py-2 px-3 text-[12px] font-semibold text-[#777777] uppercase">Supplier Account</th>
                      <th className="py-2 px-3 text-[12px] font-semibold text-[#777777] uppercase">Carrier / Fleet</th>
                      <th className="py-2 px-3 text-[12px] font-semibold text-[#777777] uppercase">Total Quote</th>
                      <th className="py-2 px-3 text-[12px] font-semibold text-[#777777] uppercase">Rank</th>
                      <th className="py-2 px-3 text-[12px] font-semibold text-[#777777] uppercase">Triggered Ext.</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E5E5]">
                    {auction.bids.map((b: any) => (
                      <tr key={b.id} className="hover:bg-[#F9F9F9]">
                        <td className="py-2 px-3 text-[12px] font-mono text-[#777777]">
                          {formatTime(b.submitted_at || b.created_at)}
                        </td>
                        <td className="py-2 px-3 text-[13px] font-medium text-[#111111]">
                          {b.supplier_company_name || '—'}
                        </td>
                        <td className="py-2 px-3 text-[13px] text-[#777777]">
                          {b.carrier_name}
                        </td>
                        <td className="py-2 px-3 text-[14px] font-mono font-medium text-[#111111]">
                          ${b.total_quote?.toLocaleString()}
                        </td>
                        <td className="py-2 px-3 text-[12px] font-medium text-[#111111]">
                          L{b.rank_at_submission}
                        </td>
                        <td className="py-2 px-3 text-[12px]">
                          {b.triggered_extension ? (
                            <span className="text-[#B36200] font-medium">+Extension</span>
                          ) : (
                            <span className="text-[#AAAAAA]">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Activity Logs for this Auction */}
          <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-4 space-y-3">
            <h2 className="text-[16px] font-semibold text-[#111111]">
              Auction Activity & Audit Trail
            </h2>
            <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
              {auction.activities?.length === 0 ? (
                <div className="text-center py-4 text-[12px] text-[#777777]">No activity logged yet.</div>
              ) : (
                auction.activities?.map((act: any) => (
                  <div
                    key={act.id}
                    className="p-2 border border-[#E5E5E5] rounded-[4px] flex items-center justify-between text-[12px]"
                  >
                    <div className="space-y-0.5">
                      <span className="font-mono text-[10px] text-[#777777] uppercase tracking-wider">
                        {act.event_type}
                      </span>
                      <p className="text-[13px] text-[#111111]">{act.description}</p>
                    </div>
                    <span className="font-mono text-[11px] text-[#777777] shrink-0">
                      {formatTime(act.created_at)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
