from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from ..models.rfq import AuctionStatus
from ..models.auction import ExtensionTriggerType


class AuctionConfigCreate(BaseModel):
    trigger_window_minutes: float = Field(10.0, gt=0, description="Trigger Window (X Minutes)")
    extension_duration_minutes: float = Field(5.0, gt=0, description="Extension Duration (Y Minutes)")
    extension_trigger_type: ExtensionTriggerType = Field(
        ExtensionTriggerType.L1_RANK_CHANGE,
        description="Option A (ANY_BID), Option B (ANY_RANK_CHANGE), Option C (L1_RANK_CHANGE)"
    )


class RFQCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="RFQ Name")
    description: Optional[str] = Field(None, description="Detailed scope or requirements")
    origin: str = Field(..., min_length=2, max_length=255)
    destination: str = Field(..., min_length=2, max_length=255)
    cargo_details: Optional[str] = Field(None, description="Equipment, container size or weight")
    pickup_service_date: datetime = Field(..., description="Pickup / Service Date")

    bid_start_time: datetime = Field(..., description="Bid Start Date & Time")
    bid_close_time: datetime = Field(..., description="Initial Bid Close Date & Time")
    forced_bid_close_time: datetime = Field(..., description="Forced Bid Close Date & Time (Hard limit)")

    is_british_auction: bool = Field(True, description="Enable British Auction toggle")
    auction_config: Optional[AuctionConfigCreate] = None
    target_price: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_rfq_schedule(self):
        if self.bid_close_time <= self.bid_start_time:
            raise ValueError("Bid Close Time must be strictly later than Bid Start Time.")
        if self.forced_bid_close_time <= self.bid_close_time:
            raise ValueError("Forced Bid Close Time must be strictly later than Bid Close Time.")
        return self


class RFQUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    cargo_details: Optional[str] = None
    target_price: Optional[float] = None


class AuctionConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trigger_window_minutes: float
    extension_duration_minutes: float
    extension_trigger_type: ExtensionTriggerType
    created_at: datetime


class RFQResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_id: str
    name: str
    description: Optional[str] = None
    buyer_id: int
    buyer_name: Optional[str] = None
    origin: str
    destination: str
    cargo_details: Optional[str] = None
    pickup_service_date: datetime
    bid_start_time: datetime
    original_bid_close_time: datetime
    current_bid_close_time: datetime
    forced_bid_close_time: datetime
    status: AuctionStatus
    is_british_auction: bool
    target_price: Optional[float] = None
    extension_count: int = 0
    current_lowest_bid: Optional[float] = None
    l1_carrier_name: Optional[str] = None
    total_bids_count: int = 0
    total_suppliers_count: int = 0
    created_at: datetime
    updated_at: datetime
    auction_config: Optional[AuctionConfigurationResponse] = None
