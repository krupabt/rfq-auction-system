import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base


class ExtensionTriggerType(str, enum.Enum):
    ANY_BID = "ANY_BID"                        # Bid Received in Last X Minutes
    ANY_RANK_CHANGE = "ANY_RANK_CHANGE"        # Any Supplier Rank Change in Last X Minutes
    L1_RANK_CHANGE = "L1_RANK_CHANGE"          # Lowest Bidder (L1) Rank Change in Last X Minutes


class AuctionStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    FORCE_CLOSED = "FORCE_CLOSED"


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    cargo_details = Column(String(255), nullable=True)
    service_date = Column(DateTime, nullable=False)  # Pickup / Service Date

    # Auction Timing
    bid_start_time = Column(DateTime, nullable=False)
    bid_close_time = Column(DateTime, nullable=False)               # Dynamic, extends on triggers
    original_bid_close_time = Column(DateTime, nullable=False)      # Baseline close time
    forced_bid_close_time = Column(DateTime, nullable=False)        # Hard limit ceiling

    # British Auction Configuration
    trigger_window_minutes = Column(Float, nullable=False, default=10.0)      # X Minutes
    extension_duration_minutes = Column(Float, nullable=False, default=5.0)   # Y Minutes
    extension_trigger_type = Column(
        Enum(ExtensionTriggerType),
        nullable=False,
        default=ExtensionTriggerType.L1_RANK_CHANGE
    )

    # Tracking & State
    extension_count = Column(Integer, default=0, nullable=False)
    target_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    quotes = relationship("Quote", back_populates="rfq", cascade="all, delete-orphan", order_by="Quote.total_charges.asc()")
    activity_logs = relationship("AuctionActivityLog", back_populates="rfq", cascade="all, delete-orphan", order_by="AuctionActivityLog.created_at.desc()")

    def get_status(self, now: datetime | None = None) -> AuctionStatus:
        """Dynamically computes the auction status based on current time."""
        if now is None:
            now = datetime.now(timezone.utc)
        
        # Ensure now is timezone-aware if comparing
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        
        # Ensure model datetimes are comparable
        start = self.bid_start_time.replace(tzinfo=timezone.utc) if self.bid_start_time.tzinfo is None else self.bid_start_time
        close = self.bid_close_time.replace(tzinfo=timezone.utc) if self.bid_close_time.tzinfo is None else self.bid_close_time
        forced_close = self.forced_bid_close_time.replace(tzinfo=timezone.utc) if self.forced_bid_close_time.tzinfo is None else self.forced_bid_close_time

        if now >= forced_close:
            return AuctionStatus.FORCE_CLOSED
        if now >= close:
            return AuctionStatus.CLOSED
        if now < start:
            return AuctionStatus.UPCOMING
        return AuctionStatus.ACTIVE


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_name = Column(String(255), nullable=False, index=True)

    # Cost breakdown
    freight_charges = Column(Float, nullable=False)
    origin_charges = Column(Float, nullable=False, default=0.0)
    destination_charges = Column(Float, nullable=False, default=0.0)
    total_charges = Column(Float, nullable=False, index=True)  # Computed: freight + origin + destination

    transit_days = Column(Integer, nullable=False)             # Transit Time
    quote_validity_date = Column(DateTime, nullable=False)     # Validity of Quote
    notes = Column(Text, nullable=True)

    rank_at_submission = Column(Integer, nullable=True)        # Rank when submitted (1=L1, 2=L2...)
    is_l1 = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="quotes")


class AuctionActivityLog(Base):
    __tablename__ = "auction_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # BID_SUBMITTED, EXTENSION_TRIGGERED, AUCTION_CREATED, STATUS_CHANGE
    carrier_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)             # Explicit explanation of extension or trigger
    old_close_time = Column(DateTime, nullable=True)
    new_close_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="activity_logs")
