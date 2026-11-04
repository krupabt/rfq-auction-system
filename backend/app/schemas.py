from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from .models import ExtensionTriggerType, AuctionStatus


class RFQCreate(BaseModel):
    reference_id: Optional[str] = Field(None, description="Unique RFQ ID or reference code")
    name: str = Field(..., min_length=2, max_length=255, description="RFQ Name")
    origin: str = Field(..., min_length=2, max_length=255, description="Origin Port / City")
    destination: str = Field(..., min_length=2, max_length=255, description="Destination Port / City")
    cargo_details: Optional[str] = Field("FCL 40' High Cube (x2) - 22,000 kg", description="Cargo or Equipment details")
    service_date: datetime = Field(..., description="Pickup / Service Date")

    # Auction Timing
    bid_start_time: datetime = Field(..., description="Bid Start Date & Time")
    bid_close_time: datetime = Field(..., description="Bid Close Date & Time")
    forced_bid_close_time: datetime = Field(..., description="Forced Bid Close Date & Time (Hard limit)")

    # British Auction Config
    trigger_window_minutes: float = Field(10.0, gt=0, description="Trigger Window (X Minutes)")
    extension_duration_minutes: float = Field(5.0, gt=0, description="Extension Duration (Y Minutes)")
    extension_trigger_type: ExtensionTriggerType = Field(
        ExtensionTriggerType.L1_RANK_CHANGE,
        description="Trigger condition for auction extension"
    )
    target_price: Optional[float] = Field(None, ge=0, description="Target/Baseline budget price")

    @model_validator(mode="after")
    def validate_auction_schedule(self):
        if self.bid_close_time <= self.bid_start_time:
            raise ValueError("Bid Close Time must be strictly later than Bid Start Time.")
        if self.forced_bid_close_time <= self.bid_close_time:
            raise ValueError("Forced Bid Close Time must be strictly later than Bid Close Time.")
        return self


class QuoteCreate(BaseModel):
    carrier_name: str = Field(..., min_length=1, max_length=255, description="Carrier / Supplier Name")
    freight_charges: float = Field(..., ge=0, description="Base Freight Charges ($)")
    origin_charges: float = Field(0.0, ge=0, description="Origin Charges / Handling ($)")
    destination_charges: float = Field(0.0, ge=0, description="Destination Charges / Terminal ($)")
    transit_days: int = Field(..., gt=0, description="Estimated Transit Time in Days")
    quote_validity_date: datetime = Field(..., description="Validity of Quote Date")
    notes: Optional[str] = Field(None, description="Optional notes or equipment guarantees")


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    event_type: str
    carrier_name: Optional[str] = None
    description: str
    reason: Optional[str] = None
    old_close_time: Optional[datetime] = None
    new_close_time: Optional[datetime] = None
    created_at: datetime


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    carrier_name: str
    freight_charges: float
    origin_charges: float
    destination_charges: float
    total_charges: float
    transit_days: int
    quote_validity_date: datetime
    notes: Optional[str] = None
    rank_at_submission: Optional[int] = None
    current_rank: Optional[int] = None
    is_l1: bool
    created_at: datetime


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    carrier_name: str
    best_quote_id: int
    freight_charges: float
    origin_charges: float
    destination_charges: float
    total_charges: float
    transit_days: int
    quote_validity_date: datetime
    quote_count: int
    last_bid_time: datetime
    is_l1: bool


class RFQSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_id: str
    name: str
    origin: str
    destination: str
    cargo_details: Optional[str] = None
    service_date: datetime
    bid_start_time: datetime
    bid_close_time: datetime
    original_bid_close_time: datetime
    forced_bid_close_time: datetime
    trigger_window_minutes: float
    extension_duration_minutes: float
    extension_trigger_type: ExtensionTriggerType
    status: AuctionStatus
    extension_count: int
    target_price: Optional[float] = None
    current_lowest_bid: Optional[float] = None
    l1_carrier_name: Optional[str] = None
    total_quotes_count: int = 0
    total_carriers_count: int = 0
    created_at: datetime


class RFQDetailResponse(RFQSummaryResponse):
    quotes: List[QuoteResponse] = []
    leaderboard: List[LeaderboardEntry] = []
    activity_logs: List[ActivityLogResponse] = []
    in_trigger_window: bool = False
    remaining_seconds: float = 0.0


class BidSubmissionResult(BaseModel):
    quote: QuoteResponse
    rfq_extended: bool
    extension_reason: Optional[str] = None
    old_close_time: Optional[datetime] = None
    new_close_time: Optional[datetime] = None
    extension_count: int
    current_status: AuctionStatus
    new_rank: int
    is_l1: bool
