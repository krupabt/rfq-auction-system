from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .rfq import RFQResponse
from .bid import BidResponse, SupplierRankingEntry
from ..models.rfq import AuctionStatus


class AuctionExtensionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    previous_close_time: datetime
    new_close_time: datetime
    extension_duration: float
    trigger_reason: str
    triggering_bid_id: Optional[int] = None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: Optional[int] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    event_type: str
    description: str
    log_metadata: Optional[str] = None
    created_at: datetime


class AuctionStatusResponse(BaseModel):
    rfq_id: int
    status: AuctionStatus
    current_bid_close_time: datetime
    forced_bid_close_time: datetime
    remaining_seconds: float
    in_trigger_window: bool
    trigger_window_minutes: float
    extension_count: int
    current_lowest_bid: Optional[float] = None
    l1_carrier_name: Optional[str] = None


class AuctionDetailResponse(RFQResponse):
    rankings: List[SupplierRankingEntry] = []
    bids: List[BidResponse] = []
    extensions: List[AuctionExtensionResponse] = []
    activities: List[ActivityLogResponse] = []
    remaining_seconds: float = 0.0
    in_trigger_window: bool = False
    my_rank: Optional[int] = None
    my_best_bid: Optional[float] = None
