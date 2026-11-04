from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from ..models.rfq import AuctionStatus


class DashboardStats(BaseModel):
    total_rfqs: int
    active_auctions: int
    closed_auctions: int
    scheduled_auctions: int
    total_suppliers: int
    total_bids_received: int
    total_extensions_triggered: int
    total_estimated_savings: float = 0.0


class RecentRFQItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_id: str
    name: str
    buyer_name: str
    lowest_bid: Optional[float] = None
    l1_carrier: Optional[str] = None
    current_closing_time: datetime
    status: AuctionStatus
    total_bids: int


class ActiveAuctionItem(BaseModel):
    id: int
    reference_id: str
    name: str
    origin: str
    destination: str
    current_lowest_bid: Optional[float] = None
    l1_carrier: Optional[str] = None
    current_closing_time: datetime
    forced_closing_time: datetime
    remaining_seconds: float
    in_trigger_window: bool
    extension_count: int
    total_bids: int


class UpcomingClosureItem(BaseModel):
    id: int
    reference_id: str
    name: str
    current_closing_time: datetime
    forced_closing_time: datetime
    remaining_seconds: float
    current_lowest_bid: Optional[float] = None
    l1_carrier: Optional[str] = None
    status: AuctionStatus


class RecentActivityItem(BaseModel):
    id: int
    rfq_id: Optional[int] = None
    rfq_ref: Optional[str] = None
    event_type: str
    description: str
    created_at: datetime
