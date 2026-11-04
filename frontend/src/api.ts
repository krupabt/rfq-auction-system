import {
  RFQSummary,
  RFQDetail,
  CreateRFQPayload,
  SubmitQuotePayload,
  BidSubmissionResult,
} from './types';

const API_BASE = '/api';

export async function fetchRFQs(statusFilter?: string): Promise<RFQSummary[]> {
  const url = statusFilter
    ? `${API_BASE}/rfqs?status_filter=${encodeURIComponent(statusFilter)}`
    : `${API_BASE}/rfqs`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch RFQs: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchRFQDetail(rfqId: number): Promise<RFQDetail> {
  const res = await fetch(`${API_BASE}/rfqs/${rfqId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch RFQ #${rfqId}`);
  }
  return res.json();
}

export async function createRFQ(payload: CreateRFQPayload): Promise<RFQSummary> {
  const res = await fetch(`${API_BASE}/rfqs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create RFQ: ${res.statusText}`);
  }
  return res.json();
}

export async function submitQuote(
  rfqId: number,
  payload: SubmitQuotePayload,
  simulatedTime?: string
): Promise<BidSubmissionResult> {
  const query = simulatedTime ? `?simulated_current_time=${encodeURIComponent(simulatedTime)}` : '';
  const res = await fetch(`${API_BASE}/rfqs/${rfqId}/quotes${query}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to submit quote: ${res.statusText}`);
  }
  return res.json();
}

export async function adjustAuctionTimeForDemo(
  rfqId: number,
  remainingMinutes: number
): Promise<{ message: string; new_bid_close_time: string }> {
  const res = await fetch(
    `${API_BASE}/rfqs/${rfqId}/adjust-time-for-demo?remaining_minutes=${remainingMinutes}`,
    { method: 'POST' }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to adjust demo time');
  }
  return res.json();
}

export async function reseedDemoData(): Promise<void> {
  await fetch(`${API_BASE}/seed`, { method: 'POST' });
}
