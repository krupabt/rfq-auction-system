import React from 'react';

interface TriggerRuleBadgeProps {
  type: string;
}

export const TriggerRuleBadge: React.FC<TriggerRuleBadgeProps> = ({ type }) => {
  const config = {
    ANY_BID: {
      label: 'Option A: Any Bid',
      desc: 'Extends when any valid quote is placed in trigger window',
    },
    ANY_RANK_CHANGE: {
      label: 'Option B: Any Rank Change',
      desc: 'Extends when any supplier standing changes',
    },
    L1_RANK_CHANGE: {
      label: 'Option C: L1 Rank Change',
      desc: 'Extends only when leading lowest bid (L1) changes',
    },
  }[type] || {
    label: type,
    desc: '',
  };

  return (
    <span
      title={config.desc}
      className="inline-flex items-center px-2 py-0.5 rounded-[4px] text-xs font-mono font-medium bg-[#F9FAFB] text-[#111111] border border-[#E5E5E5]"
    >
      {config.label}
    </span>
  );
};
