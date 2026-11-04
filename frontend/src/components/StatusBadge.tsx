import React from 'react';

export type AuctionStatusType = 'SCHEDULED' | 'ACTIVE' | 'CLOSED' | 'FORCE_CLOSED';

interface StatusBadgeProps {
  status: AuctionStatusType | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status ? status.toUpperCase() : 'SCHEDULED';

  const config = {
    ACTIVE: {
      label: 'Active',
      className: 'bg-[#F0FDF4] text-[#166534] border-[#BBF7D0]',
      dot: 'bg-[#16A34A]',
    },
    SCHEDULED: {
      label: 'Scheduled',
      className: 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]',
      dot: 'bg-[#D97706]',
    },
    CLOSED: {
      label: 'Closed',
      className: 'bg-[#F9FAFB] text-[#4B5563] border-[#E5E7EB]',
      dot: 'bg-[#9CA3AF]',
    },
    FORCE_CLOSED: {
      label: 'Force Closed',
      className: 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]',
      dot: 'bg-[#DC2626]',
    },
  }[normalized] || {
    label: normalized,
    className: 'bg-[#F9FAFB] text-[#4B5563] border-[#E5E7EB]',
    dot: 'bg-[#9CA3AF]',
  };

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-0.5 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-[4px] font-medium border ${config.className} ${sizeClasses}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
};
