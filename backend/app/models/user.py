import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    BUYER = "BUYER"
    SUPPLIER = "SUPPLIER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.BUYER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    supplier_profile = relationship("Supplier", back_populates="user", uselist=False, cascade="all, delete-orphan")
    rfqs = relationship("RFQ", back_populates="buyer", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    company_name = Column(String(255), unique=True, index=True, nullable=False)
    contact_person = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="supplier_profile")
    bids = relationship("Bid", back_populates="supplier", cascade="all, delete-orphan")
