import React, { useState, useEffect } from 'react';

interface CountdownTimerProps {
  closeTime: string;
  forcedCloseTime: string;
  triggerWindowMinutes?: number;
  status: string;
  compact?: boolean;
  onExpire?: () => void;
}

export const CountdownTimer: React.FC<CountdownTimerProps> = ({
  closeTime,
  forcedCloseTime,
  triggerWindowMinutes = 10,
  status,
  compact = false,
  onExpire,
}) => {
  const [remaining, setRemaining] = useState<{
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
    totalSeconds: number;
    isTriggerWindow: boolean;
    isForceClosed: boolean;
    isClosed: boolean;
  }>({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    totalSeconds: 0,
    isTriggerWindow: false,
    isForceClosed: false,
    isClosed: false,
  });

  const prevDiffRef = React.useRef<number | null>(null);

  useEffect(() => {
    const calculateTime = () => {
      const now = new Date().getTime();
      const close = new Date(closeTime).getTime();
      const forced = new Date(forcedCloseTime).getTime();

      const diffToClose = Math.max(0, Math.floor((close - now) / 1000));
      const diffToForced = Math.max(0, Math.floor((forced - now) / 1000));

      const isForceClosed = status === 'FORCE_CLOSED' || diffToForced <= 0;
      const isClosed = status === 'CLOSED' || isForceClosed || diffToClose <= 0;
      const isTriggerWindow = !isClosed && diffToClose <= triggerWindowMinutes * 60;

      const days = Math.floor(diffToClose / (3600 * 24));
      const hours = Math.floor((diffToClose % (3600 * 24)) / 3600);
      const minutes = Math.floor((diffToClose % 3600) / 60);
      const seconds = diffToClose % 60;

      setRemaining({
        days,
        hours,
        minutes,
        seconds,
        totalSeconds: diffToClose,
        isTriggerWindow,
        isForceClosed,
        isClosed,
      });

      if (prevDiffRef.current !== null && prevDiffRef.current > 0 && diffToClose <= 0 && onExpire) {
        onExpire();
      }
      prevDiffRef.current = diffToClose;
    };

    calculateTime();
    const interval = setInterval(calculateTime, 1000);
    return () => clearInterval(interval);
  }, [closeTime, forcedCloseTime, triggerWindowMinutes, status, onExpire]);

  const pad = (n: number) => n.toString().padStart(2, '0');

  if (compact) {
    if (remaining.isForceClosed) {
      return (
        <span className="font-mono text-xs font-medium text-[#991B1B]">
          Force Closed
        </span>
      );
    }
    if (remaining.isClosed) {
      return (
        <span className="font-mono text-xs text-[#777777]">
          00:00:00
        </span>
      );
    }

    const formatted = remaining.days > 0
      ? `${remaining.days}d ${pad(remaining.hours)}:${pad(remaining.minutes)}:${pad(remaining.seconds)}`
      : `${pad(remaining.hours)}:${pad(remaining.minutes)}:${pad(remaining.seconds)}`;

    return (
      <div className="flex items-center gap-2">
        <span
          className={`font-mono text-xs font-medium ${
            remaining.isTriggerWindow ? 'text-[#D97706] font-semibold' : 'text-[#111111]'
          }`}
        >
          {formatted}
        </span>
        {remaining.isTriggerWindow && (
          <span className="text-[10px] font-medium uppercase tracking-wider text-[#92400E] bg-[#FFFBEB] px-1.5 py-0.5 rounded-[4px] border border-[#FDE68A]">
            Trigger Window
          </span>
        )}
      </div>
    );
  }

  // Full Auction Detail Countdown Display
  return (
    <div
      className={`rounded-[6px] border p-4 bg-white transition-colors ${
        remaining.isTriggerWindow ? 'border-[#F59E0B]' : 'border-[#E5E5E5]'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#777777]">
          Auction Countdown
        </span>
        {remaining.isTriggerWindow && !remaining.isClosed && (
          <span className="text-xs font-medium text-[#92400E] bg-[#FFFBEB] px-2 py-0.5 rounded-[4px] border border-[#FDE68A]">
            Inside Trigger Window (Last {triggerWindowMinutes}m)
          </span>
        )}
        {remaining.isForceClosed && (
          <span className="text-xs font-medium text-[#991B1B] bg-[#FEF2F2] px-2 py-0.5 rounded-[4px] border border-[#FECACA]">
            Hard Cap Reached
          </span>
        )}
      </div>

      {/* Time Units Display */}
      <div className="grid grid-cols-4 gap-2 text-center my-2">
        <div className="border border-[#E5E5E5] rounded-[4px] p-2 bg-[#FAFAFA]">
          <span className="font-mono text-xl font-semibold text-[#111111] block">
            {pad(remaining.days)}
          </span>
          <span className="text-[11px] text-[#777777]">Days</span>
        </div>
        <div className="border border-[#E5E5E5] rounded-[4px] p-2 bg-[#FAFAFA]">
          <span className="font-mono text-xl font-semibold text-[#111111] block">
            {pad(remaining.hours)}
          </span>
          <span className="text-[11px] text-[#777777]">Hours</span>
        </div>
        <div className="border border-[#E5E5E5] rounded-[4px] p-2 bg-[#FAFAFA]">
          <span className="font-mono text-xl font-semibold text-[#111111] block">
            {pad(remaining.minutes)}
          </span>
          <span className="text-[11px] text-[#777777]">Mins</span>
        </div>
        <div className="border border-[#E5E5E5] rounded-[4px] p-2 bg-[#FAFAFA]">
          <span className="font-mono text-xl font-semibold text-[#111111] block">
            {pad(remaining.seconds)}
          </span>
          <span className="text-[11px] text-[#777777]">Secs</span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-[#E5E5E5] flex flex-wrap items-center justify-between text-xs text-[#777777]">
        <span>
          Forced Close Limit: <strong className="text-[#111111] font-mono">{new Date(forcedCloseTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</strong>
        </span>
        <span>Extensions cannot exceed forced close</span>
      </div>
    </div>
  );
};
