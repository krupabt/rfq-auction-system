export type ExtensionTriggerType = 'ANY_BID' | 'ANY_RANK_CHANGE' | 'L1_RANK_CHANGE';

export type AuctionStatus = 'UPCOMING' | 'ACTIVE' | 'CLOSED' | 'FORCE_CLOSED';

export interface RFQSummary {
  id: number;
  reference_id: string;
  name: string;
  origin: string;
  destination: string;
  cargo_details?: string;
  service_date: string;
  bid_start_time: string;
  bid_close_time: string;
  original_bid_close_time: string;
  forced_bid_close_time: string;
  trigger_window_minutes: number;
  extension_duration_minutes: number;
  extension_trigger_type: ExtensionTriggerType;
  status: AuctionStatus;
  extension_count: number;
  target_price?: number;
  current_lowest_bid?: number;
  l1_carrier_name?: string;
  total_quotes_count: number;
  total_carriers_count: number;
  created_at: string;
}

export interface Quote {
  id: number;
  rfq_id: number;
  carrier_name: string;
  freight_charges: number;
  origin_charges: number;
  destination_charges: number;
  total_charges: number;
  transit_days: number;
  quote_validity_date: string;
  notes?: string;
  rank_at_submission?: number;
  current_rank?: number;
  is_l1: boolean;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  carrier_name: string;
  best_quote_id: number;
  freight_charges: number;
  origin_charges: number;
  destination_charges: number;
  total_charges: number;
  transit_days: number;
  quote_validity_date: string;
  quote_count: number;
  last_bid_time: string;
  is_l1: boolean;
}

export interface ActivityLog {
  id: number;
  rfq_id: number;
  event_type: string;
  carrier_name?: string;
  description: string;
  reason?: string;
  old_close_time?: string;
  new_close_time?: string;
  created_at: string;
}

export interface RFQDetail extends RFQSummary {
  quotes: Quote[];
  leaderboard: LeaderboardEntry[];
  activity_logs: ActivityLog[];
  in_trigger_window: boolean;
  remaining_seconds: number;
}

export interface CreateRFQPayload {
  reference_id?: string;
  name: string;
  origin: string;
  destination: string;
  cargo_details?: string;
  service_date: string;
  bid_start_time: string;
  bid_close_time: string;
  forced_bid_close_time: string;
  trigger_window_minutes: number;
  extension_duration_minutes: number;
  extension_trigger_type: ExtensionTriggerType;
  target_price?: number;
}

export interface SubmitQuotePayload {
  carrier_name: string;
  freight_charges: number;
  origin_charges: number;
  destination_charges: number;
  transit_days: number;
  quote_validity_date: string;
  notes?: string;
}

export interface BidSubmissionResult {
  quote: Quote;
  rfq_extended: boolean;
  extension_reason?: string;
  old_close_time?: string;
  new_close_time?: string;
  extension_count: number;
  current_status: AuctionStatus;
  new_rank: number;
  is_l1: boolean;
}
