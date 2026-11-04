from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BidCreate(BaseModel):
    carrier_name: str = Field(..., min_length=1, max_length=255, description="Carrier / Fleet operator name")
    freight_charges: float = Field(..., ge=0, description="Base Freight Charges")
    origin_charges: float = Field(0.0, ge=0, description="Origin Terminal & Handling Charges")
    destination_charges: float = Field(0.0, ge=0, description="Destination Terminal & Port Charges")
    transit_time: int = Field(..., gt=0, description="Estimated Transit Time in Days")
    validity_of_quote: datetime = Field(..., description="Validity of Quote Expiry Date")
    notes: Optional[str] = Field(None, description="Demurrage, equipment or service guarantees")


class BidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    supplier_id: int
    carrier_name: str
    supplier_company_name: Optional[str] = None
    freight_charges: float
    origin_charges: float
    destination_charges: float
    total_quote: float
    transit_time: int
    validity_of_quote: datetime
    notes: Optional[str] = None
    submitted_at: datetime
    created_at: Optional[datetime] = None  # alias for frontend compatibility
    is_valid: bool
    rank_at_submission: Optional[int] = None
    is_l1: bool = False
    triggered_extension: bool = False


class SupplierRankingEntry(BaseModel):
    rank: int
    rank_label: str  # L1, L2, L3, ...
    supplier_id: int
    supplier_name: str
    company_name: Optional[str] = None  # alias for frontend compatibility
    carrier_name: str
    best_bid_id: int
    freight_charges: float
    origin_charges: float
    destination_charges: float
    total_quote: float
    transit_time: int
    validity_of_quote: datetime
    total_bids_placed: int
    last_bid_time: datetime
    last_bid_at: Optional[datetime] = None  # alias for frontend compatibility
    is_l1: bool
