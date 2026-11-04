from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models.rfq import RFQ, AuctionStatus
from ..models.user import User, Supplier, UserRole
from ..models.bid import Bid
from ..models.auction import AuctionExtension
from ..models.activity import ActivityLog
from ..schemas.dashboard import (
    DashboardStats,
    RecentRFQItem,
    ActiveAuctionItem,
    UpcomingClosureItem,
    RecentActivityItem
)
from ..services.ranking_service import compute_supplier_rankings, ensure_utc
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    rfqs = db.query(RFQ).all()

    active_cnt = 0
    closed_cnt = 0
    scheduled_cnt = 0
    total_savings = 0.0

    for r in rfqs:
        st = r.compute_current_status(now)
        if st == AuctionStatus.ACTIVE:
            active_cnt += 1
        elif st in (AuctionStatus.CLOSED, AuctionStatus.FORCE_CLOSED):
            closed_cnt += 1
        elif st == AuctionStatus.SCHEDULED:
            scheduled_cnt += 1

        # Calculate estimated savings if target price exists and quotes were placed
        if r.target_price and r.bids:
            lowest = min(b.total_quote for b in r.bids if b.is_valid)
            if lowest < r.target_price:
                total_savings += (r.target_price - lowest)

    total_suppliers = db.query(Supplier).count()
    total_bids = db.query(Bid).filter(Bid.is_valid == True).count()
    total_extensions = db.query(AuctionExtension).count()

    return DashboardStats(
        total_rfqs=len(rfqs),
        active_auctions=active_cnt,
        closed_auctions=closed_cnt,
        scheduled_auctions=scheduled_cnt,
        total_suppliers=total_suppliers,
        total_bids_received=total_bids,
        total_extensions_triggered=total_extensions,
        total_estimated_savings=round(total_savings, 2)
    )


@router.get("/recent-rfqs", response_model=List[RecentRFQItem])
def get_recent_rfqs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    rfqs = db.query(RFQ).order_by(desc(RFQ.created_at)).limit(6).all()

    items = []
    for r in rfqs:
        status_computed = r.compute_current_status(now)
        _, l1_name, l1_price = compute_supplier_rankings(r)

        items.append(RecentRFQItem(
            id=r.id,
            reference_id=r.reference_id,
            name=r.name,
            buyer_name=r.buyer.full_name if r.buyer else "Buyer",
            lowest_bid=l1_price,
            l1_carrier=l1_name,
            current_closing_time=ensure_utc(r.current_bid_close_time),
            status=status_computed,
            total_bids=len(r.bids)
        ))

    return items


@router.get("/active-auctions", response_model=List[ActiveAuctionItem])
def get_active_auctions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    rfqs = db.query(RFQ).filter(RFQ.is_british_auction == True).all()

    active_items = []
    for r in rfqs:
        st = r.compute_current_status(now)
        if st == AuctionStatus.ACTIVE:
            _, l1_name, l1_price = compute_supplier_rankings(r)
            close_utc = ensure_utc(r.current_bid_close_time)
            rem_secs = max(0.0, (close_utc - now).total_seconds())

            in_window = False
            if r.auction_config:
                window_secs = r.auction_config.trigger_window_minutes * 60.0
                in_window = rem_secs <= window_secs

            active_items.append(ActiveAuctionItem(
                id=r.id,
                reference_id=r.reference_id,
                name=r.name,
                origin=r.origin,
                destination=r.destination,
                current_lowest_bid=l1_price,
                l1_carrier=l1_name,
                current_closing_time=close_utc,
                forced_closing_time=ensure_utc(r.forced_bid_close_time),
                remaining_seconds=rem_secs,
                in_trigger_window=in_window,
                extension_count=len(r.extensions),
                total_bids=len(r.bids)
            ))

    active_items.sort(key=lambda x: x.remaining_seconds)
    return active_items[:6]


@router.get("/upcoming-closures", response_model=List[UpcomingClosureItem])
def get_upcoming_closures(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    rfqs = db.query(RFQ).all()

    items = []
    for r in rfqs:
        st = r.compute_current_status(now)
        if st in (AuctionStatus.ACTIVE, AuctionStatus.SCHEDULED):
            close_utc = ensure_utc(r.current_bid_close_time)
            rem_secs = max(0.0, (close_utc - now).total_seconds())
            _, l1_name, l1_price = compute_supplier_rankings(r)

            items.append(UpcomingClosureItem(
                id=r.id,
                reference_id=r.reference_id,
                name=r.name,
                current_closing_time=close_utc,
                forced_closing_time=ensure_utc(r.forced_bid_close_time),
                remaining_seconds=rem_secs,
                current_lowest_bid=l1_price,
                l1_carrier=l1_name,
                status=st
            ))

    items.sort(key=lambda x: x.remaining_seconds)
    return items[:5]


@router.get("/recent-activities", response_model=List[RecentActivityItem])
def get_recent_activities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(10).all()
    return [
        RecentActivityItem(
            id=log.id,
            rfq_id=log.rfq_id,
            rfq_ref=log.rfq.reference_id if log.rfq else None,
            event_type=log.event_type,
            description=log.description,
            created_at=ensure_utc(log.created_at)
        )
        for log in logs
    ]
