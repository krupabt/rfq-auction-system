from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class AuctionSummaryItem(BaseModel):
    rfq_id: int
    reference_id: str
    name: str
    status: str
    winning_supplier: Optional[str] = None
    final_lowest_quote: Optional[float] = None
    target_price: Optional[float] = None
    savings_amount: Optional[float] = None
    savings_percentage: Optional[float] = None
    total_bids: int
    total_extensions: int
    duration_hours: float


class SupplierPerformanceItem(BaseModel):
    supplier_id: int
    company_name: str
    contact_person: str
    total_auctions_participated: int
    total_bids_placed: int
    auctions_won: int
    win_rate_percentage: float
    average_discount_percentage: float


class ReportAnalyticsResponse(BaseModel):
    total_auctions: int
    completed_auctions: int
    active_auctions: int
    total_bids: int
    average_bids_per_auction: float
    average_extensions_per_auction: float
    total_savings_generated: float
    status_distribution: Dict[str, int]
    trigger_type_distribution: Dict[str, int]
    top_suppliers: List[Dict[str, Any]]
    auction_summaries: List[AuctionSummaryItem]
