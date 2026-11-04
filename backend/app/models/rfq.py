import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class AuctionStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    FORCE_CLOSED = "FORCE_CLOSED"


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    buyer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Route & Cargo details
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    cargo_details = Column(String(255), nullable=True)
    pickup_service_date = Column(DateTime, nullable=False)

    # Auction Timing
    bid_start_time = Column(DateTime, nullable=False)
    original_bid_close_time = Column(DateTime, nullable=False)
    current_bid_close_time = Column(DateTime, nullable=False, index=True)
    forced_bid_close_time = Column(DateTime, nullable=False)

    status = Column(Enum(AuctionStatus), nullable=False, default=AuctionStatus.SCHEDULED)
    is_british_auction = Column(Boolean, default=True, nullable=False)
    target_price = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    buyer = relationship("User", back_populates="rfqs")
    auction_config = relationship("AuctionConfiguration", back_populates="rfq", uselist=False, cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="rfq", cascade="all, delete-orphan", order_by="Bid.total_quote.asc()")
    extensions = relationship("AuctionExtension", back_populates="rfq", cascade="all, delete-orphan", order_by="AuctionExtension.created_at.desc()")
    activity_logs = relationship("ActivityLog", back_populates="rfq", cascade="all, delete-orphan", order_by="ActivityLog.created_at.desc()")

    def compute_current_status(self, now: datetime | None = None) -> AuctionStatus:
        """
        Dynamically determines the auction status at a specific moment in time.
        IMPORTANT: An auction only becomes FORCE_CLOSED if bidding reached or hit the forced close time limit.
        If current time is past close time, it is CLOSED.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        start = self.bid_start_time.replace(tzinfo=timezone.utc) if self.bid_start_time.tzinfo is None else self.bid_start_time
        close = self.current_bid_close_time.replace(tzinfo=timezone.utc) if self.current_bid_close_time.tzinfo is None else self.current_bid_close_time
        forced = self.forced_bid_close_time.replace(tzinfo=timezone.utc) if self.forced_bid_close_time.tzinfo is None else self.forced_bid_close_time

        if now < start:
            return AuctionStatus.SCHEDULED

        # If it reached forced close cap
        if close >= forced and now >= forced:
            return AuctionStatus.FORCE_CLOSED

        if now >= close:
            return AuctionStatus.CLOSED

        return AuctionStatus.ACTIVE
