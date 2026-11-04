import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class ExtensionTriggerType(str, enum.Enum):
    ANY_BID = "ANY_BID"                        # Option A: Bid Received in Last X Minutes
    ANY_RANK_CHANGE = "ANY_RANK_CHANGE"        # Option B: Any Supplier Rank Change in Last X Minutes
    L1_RANK_CHANGE = "L1_RANK_CHANGE"          # Option C: Lowest Bidder (L1) Rank Change in Last X Minutes


class AuctionConfiguration(Base):
    __tablename__ = "auction_configurations"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # British Auction settings
    trigger_window_minutes = Column(Float, nullable=False, default=10.0)      # X Minutes
    extension_duration_minutes = Column(Float, nullable=False, default=5.0)   # Y Minutes
    extension_trigger_type = Column(
        Enum(ExtensionTriggerType),
        nullable=False,
        default=ExtensionTriggerType.L1_RANK_CHANGE
    )
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="auction_config")


class AuctionExtension(Base):
    __tablename__ = "auction_extensions"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_close_time = Column(DateTime, nullable=False)
    new_close_time = Column(DateTime, nullable=False)
    extension_duration = Column(Float, nullable=False)  # Minutes added
    trigger_reason = Column(Text, nullable=False)
    triggering_bid_id = Column(Integer, ForeignKey("bids.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="extensions")
    triggering_bid = relationship("Bid")
