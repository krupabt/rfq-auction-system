import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { ArrowLeft, AlertCircle } from 'lucide-react';

export const CreateRFQPage: React.FC = () => {
  const navigate = useNavigate();

  // Helper for default local dates
  const getInitialDates = () => {
    const now = new Date();
    const pad = (n: number) => n.toString().padStart(2, '0');
    const toInputVal = (d: Date) =>
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;

    const start = new Date(now.getTime());
    const close = new Date(now.getTime() + 30 * 60 * 1000); // +30m
    const forced = new Date(now.getTime() + 60 * 60 * 1000); // +60m
    const service = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000); // +14d

    return {
      start: toInputVal(start),
      close: toInputVal(close),
      forced: toInputVal(forced),
      service: toInputVal(service),
    };
  };

  const initial = getInitialDates();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [cargoDetails, setCargoDetails] = useState('');
  const [pickupServiceDate, setPickupServiceDate] = useState(initial.service);

  // Auction timing
  const [bidStartTime, setBidStartTime] = useState(initial.start);
  const [bidCloseTime, setBidCloseTime] = useState(initial.close);
  const [forcedBidCloseTime, setForcedBidCloseTime] = useState(initial.forced);

  // British Auction Configuration toggle
  const [isBritishAuction, setIsBritishAuction] = useState(true);
  const [triggerWindowMinutes, setTriggerWindowMinutes] = useState(10);
  const [extensionDurationMinutes, setExtensionDurationMinutes] = useState(5);
  const [extensionTriggerType, setExtensionTriggerType] = useState<'ANY_BID' | 'ANY_RANK_CHANGE' | 'L1_RANK_CHANGE'>('L1_RANK_CHANGE');
  const [targetPrice, setTargetPrice] = useState<number | ''>('');

  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const startDate = new Date(bidStartTime);
    const closeDate = new Date(bidCloseTime);
    const forcedDate = new Date(forcedBidCloseTime);

    if (!name.trim()) {
      setError('RFQ Name is required.');
      return;
    }
    if (closeDate <= startDate) {
      setError('Bid Close Time must be strictly later than Bid Start Time.');
      return;
    }
    if (forcedDate <= closeDate) {
      setError('Validation Rule: Forced Bid Close Time must always be greater than Bid Close Time.');
      return;
    }
    if (isBritishAuction) {
      if (Number(triggerWindowMinutes) <= 0) {
        setError('Trigger Window (X) must be greater than 0 minutes.');
        return;
      }
      if (Number(extensionDurationMinutes) <= 0) {
        setError('Extension Duration (Y) must be greater than 0 minutes.');
        return;
      }
    }

    setIsLoading(true);
    try {
      const payload = {
        name: name.trim(),
        description: description.trim() || undefined,
        origin: origin.trim(),
        destination: destination.trim(),
        cargo_details: cargoDetails.trim() || undefined,
        pickup_service_date: new Date(pickupServiceDate).toISOString(),
        bid_start_time: startDate.toISOString(),
        bid_close_time: closeDate.toISOString(),
        forced_bid_close_time: forcedDate.toISOString(),
        is_british_auction: isBritishAuction,
        auction_config: isBritishAuction
          ? {
              trigger_window_minutes: Number(triggerWindowMinutes),
              extension_duration_minutes: Number(extensionDurationMinutes),
              extension_trigger_type: extensionTriggerType,
            }
          : undefined,
        target_price: targetPrice ? Number(targetPrice) : undefined,
      };

      await api.post('/rfqs', payload);
      navigate('/rfqs');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create RFQ.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#E5E5E5]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/rfqs')}
            className="p-1.5 border border-[#E5E5E5] rounded-[4px] text-[#111111] hover:bg-[#F9F9F9]"
            title="Back to RFQs"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-[24px] font-semibold text-[#111111]">Create RFQ</h1>
            <p className="text-[14px] text-[#777777]">
              Specify shipment parameters, schedule and British Auction extension rules.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-white border border-red-300 rounded-[4px] text-[14px] text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: RFQ Scope & Shipment Details */}
        <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-6 space-y-4">
          <h2 className="text-[16px] font-semibold text-[#111111]">
            1. Shipment Scope & Route
          </h2>

          <div>
            <label className="block text-[14px] font-medium text-[#111111] mb-1">
              RFQ Name *
            </label>
            <input
              type="text"
              placeholder="e.g. FCL 40ft High Cube: Shanghai Port to Nhava Sheva"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Origin Port / City *
              </label>
              <input
                type="text"
                placeholder="e.g. Shanghai Port, China (CNSHA)"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                required
              />
            </div>
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Destination Port / City *
              </label>
              <input
                type="text"
                placeholder="e.g. Jawaharlal Nehru Port, India (INNSA)"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Cargo / Equipment Details
              </label>
              <input
                type="text"
                placeholder="e.g. 2x 40' HC Containers - 22,000 kg"
                value={cargoDetails}
                onChange={(e) => setCargoDetails(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
              />
            </div>
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Pickup / Service Date *
              </label>
              <input
                type="datetime-local"
                value={pickupServiceDate}
                onChange={(e) => setPickupServiceDate(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[14px] font-medium text-[#111111] mb-1">
              Description & Requirements
            </label>
            <textarea
              rows={2}
              placeholder="Specify demurrage free days, transshipment constraints, cargo handling terms..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
            />
          </div>
        </div>

        {/* Section 2: Auction Schedule & Forced Close */}
        <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-[16px] font-semibold text-[#111111]">
              2. Bidding Schedule & Forced Close Limits
            </h2>
            <span className="text-[12px] text-[#777777]">
              Forced Close &gt; Bid Close &gt; Bid Start
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Bid Start Time *
              </label>
              <input
                type="datetime-local"
                value={bidStartTime}
                onChange={(e) => setBidStartTime(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                required
              />
            </div>
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Bid Close Time *
              </label>
              <input
                type="datetime-local"
                value={bidCloseTime}
                onChange={(e) => setBidCloseTime(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                required
              />
            </div>
            <div>
              <label className="block text-[14px] font-medium text-[#111111] mb-1">
                Forced Close Time *
              </label>
              <input
                type="datetime-local"
                value={forcedBidCloseTime}
                onChange={(e) => setForcedBidCloseTime(e.target.value)}
                className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                required
              />
              <span className="text-[12px] text-[#777777] mt-1 block">
                Hard ceiling: bidding stops permanently at this time.
              </span>
            </div>
          </div>
        </div>

        {/* Section 3: British Auction Configuration */}
        <div className="bg-white border border-[#E5E5E5] rounded-[4px] p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E5]">
            <div>
              <h2 className="text-[16px] font-semibold text-[#111111]">
                3. British Auction Auto-Extension Rules
              </h2>
              <p className="text-[14px] text-[#777777]">
                Controls automated extension when competitive activity occurs near closing.
              </p>
            </div>
            <label className="flex items-center gap-2 cursor-pointer text-[14px] font-medium text-[#111111]">
              <input
                type="checkbox"
                checked={isBritishAuction}
                onChange={(e) => setIsBritishAuction(e.target.checked)}
                className="h-4 w-4 rounded accent-[#111111]"
              />
              <span>Enable British Auction</span>
            </label>
          </div>

          {isBritishAuction && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[14px] font-medium text-[#111111] mb-1">
                    Trigger Window (X Minutes) *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={triggerWindowMinutes}
                    onChange={(e) => setTriggerWindowMinutes(Number(e.target.value))}
                    className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                  <span className="text-[12px] text-[#777777] mt-1 block">
                    Monitors quote activity in the final X minutes before scheduled close.
                  </span>
                </div>

                <div>
                  <label className="block text-[14px] font-medium text-[#111111] mb-1">
                    Extension Duration (Y Minutes) *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={extensionDurationMinutes}
                    onChange={(e) => setExtensionDurationMinutes(Number(e.target.value))}
                    className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                    required
                  />
                  <span className="text-[12px] text-[#777777] mt-1 block">
                    Added to current close time whenever a trigger condition is met.
                  </span>
                </div>
              </div>

              {/* Trigger Options */}
              <div>
                <label className="block text-[14px] font-medium text-[#111111] mb-2">
                  Extension Trigger Condition *
                </label>
                <div className="space-y-2">
                  {[
                    {
                      id: 'L1_RANK_CHANGE',
                      title: 'Option C: Lowest Bidder (L1) Rank Change in Last X Minutes (Recommended)',
                      desc: 'Auction extends only when a supplier beats the overall lowest quote (L1). Focuses extensions strictly on winning price improvements.',
                    },
                    {
                      id: 'ANY_RANK_CHANGE',
                      title: 'Option B: Any Supplier Rank Change in Last X Minutes',
                      desc: 'Auction extends whenever any change occurs in supplier rankings (e.g., L3 overtakes L2).',
                    },
                    {
                      id: 'ANY_BID',
                      title: 'Option A: Bid Received in Last X Minutes',
                      desc: 'Auction extends whenever any valid quote is placed during the trigger window.',
                    },
                  ].map((opt) => (
                    <label
                      key={opt.id}
                      className={`block p-3 border rounded-[4px] cursor-pointer transition-colors ${
                        extensionTriggerType === opt.id
                          ? 'border-[#111111] bg-[#FBFBFB]'
                          : 'border-[#E5E5E5] bg-white hover:bg-[#F9F9F9]'
                      }`}
                    >
                      <div className="flex items-start gap-2.5">
                        <input
                          type="radio"
                          name="trigger_type"
                          value={opt.id}
                          checked={extensionTriggerType === opt.id}
                          onChange={() => setExtensionTriggerType(opt.id as any)}
                          className="mt-1 accent-[#111111]"
                        />
                        <div>
                          <div className="text-[14px] font-medium text-[#111111]">{opt.title}</div>
                          <div className="text-[12px] text-[#777777] mt-0.5">{opt.desc}</div>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Target Price */}
              <div>
                <label className="block text-[14px] font-medium text-[#111111] mb-1">
                  Target Price / Budget ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="e.g. 2500"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full px-3 py-2 text-[14px] text-[#111111] bg-white border border-[#E5E5E5] rounded-[4px] focus:outline-none focus:border-[#111111]"
                />
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate('/rfqs')}
            className="px-4 py-2 border border-[#E5E5E5] text-[#111111] bg-white hover:bg-[#F9F9F9] rounded-[4px] text-[14px] font-medium"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-2 bg-[#111111] hover:bg-black text-white rounded-[4px] text-[14px] font-medium disabled:bg-[#777777]"
          >
            {isLoading ? 'Creating RFQ...' : 'Create RFQ'}
          </button>
        </div>
      </form>
    </div>
  );
};
