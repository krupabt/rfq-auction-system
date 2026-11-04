from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_name = Column(String(255), nullable=False)

    # Cost breakdown
    freight_charges = Column(Float, nullable=False)
    origin_charges = Column(Float, nullable=False, default=0.0)
    destination_charges = Column(Float, nullable=False, default=0.0)
    total_quote = Column(Float, nullable=False, index=True)  # freight + origin + destination

    transit_time = Column(Integer, nullable=False)  # in days
    validity_of_quote = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)

    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    is_valid = Column(Boolean, default=True, nullable=False)
    rank_at_submission = Column(Integer, nullable=True)

    # Relationships
    rfq = relationship("RFQ", back_populates="bids")
    supplier = relationship("Supplier", back_populates="bids")
