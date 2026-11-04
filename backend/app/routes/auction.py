from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models.rfq import RFQ, AuctionStatus
from ..models.auction import AuctionExtension
from ..models.activity import ActivityLog
from ..models.user import User, UserRole
from ..models.bid import Bid
from ..schemas.rfq import RFQResponse
from ..schemas.auction import (
    AuctionDetailResponse,
    AuctionExtensionResponse,
    AuctionStatusResponse,
    ActivityLogResponse
)
from ..schemas.bid import SupplierRankingEntry, BidResponse
from ..services.ranking_service import compute_supplier_rankings, ensure_utc
from ..services.websocket_manager import ws_manager
from ..dependencies import get_current_user
from .rfq import build_rfq_response

router = APIRouter(prefix="/api/auctions", tags=["Auctions"])


@router.get("", response_model=List[RFQResponse])
def list_auctions(
    status_filter: Optional[str] = Query(None, description="SCHEDULED, ACTIVE, CLOSED, FORCE_CLOSED"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("closing_time", description="closing_time, lowest_bid, created_at"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(RFQ).filter(RFQ.is_british_auction == True)
    rfqs = query.all()
    now = datetime.now(timezone.utc)

    summaries = [build_rfq_response(r) for r in rfqs]

    # Filter
    if status_filter:
        summaries = [s for s in summaries if s.status.value.upper() == status_filter.upper()]
    if search:
        q = search.lower()
        summaries = [
            s for s in summaries
            if q in s.name.lower() or q in s.reference_id.lower() or q in s.origin.lower() or q in s.destination.lower()
        ]

    # Sort
    if sort_by == "lowest_bid":
        summaries.sort(key=lambda x: (x.current_lowest_bid is None, x.current_lowest_bid or float("inf")))
    elif sort_by == "created_at":
        summaries.sort(key=lambda x: x.created_at, reverse=True)
    else:  # closing_time
        summaries.sort(key=lambda x: x.current_bid_close_time)

    return summaries


@router.get("/{rfq_id}", response_model=AuctionDetailResponse)
def get_auction_details(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="Auction not found")

    now = datetime.now(timezone.utc)
    rfq_summary = build_rfq_response(rfq)
    rankings, _, _ = compute_supplier_rankings(rfq, db=db)

    # Calculate remaining time & trigger window
    close_utc = ensure_utc(rfq.current_bid_close_time)
    remaining_secs = max(0.0, (close_utc - now).total_seconds())

    in_trigger_window = False
    if rfq.auction_config:
        window_secs = rfq.auction_config.trigger_window_minutes * 60.0
        in_trigger_window = (remaining_secs > 0) and (remaining_secs <= window_secs)

    # Map bids chronologically descending (newest quote first for Quote History)
    chronological_bids = db.query(Bid).filter(Bid.rfq_id == rfq.id).order_by(Bid.submitted_at.desc()).all()
    bid_responses = []

    # Map supplier rank lookup
    supplier_rank_map = {r.supplier_id: r.rank for r in rankings}

    # If supplier is logged in, find their own rank & best bid
    my_rank = None
    my_best_bid = None
    if current_user.role == UserRole.SUPPLIER and current_user.supplier_profile:
        my_s_id = current_user.supplier_profile.id
        my_rank = supplier_rank_map.get(my_s_id)
        supplier_own_bids = [b.total_quote for b in chronological_bids if b.supplier_id == my_s_id and b.is_valid]
        if supplier_own_bids:
            my_best_bid = min(supplier_own_bids)

    extension_bid_ids = {ext.triggering_bid_id for ext in rfq.extensions if ext.triggering_bid_id}

    for b in chronological_bids:
        supplier_name = b.supplier.company_name if b.supplier else b.carrier_name
        b_resp = BidResponse(
            id=b.id,
            rfq_id=b.rfq_id,
            supplier_id=b.supplier_id,
            carrier_name=b.carrier_name,
            supplier_company_name=supplier_name,
            freight_charges=b.freight_charges,
            origin_charges=b.origin_charges,
            destination_charges=b.destination_charges,
            total_quote=b.total_quote,
            transit_time=b.transit_time,
            validity_of_quote=ensure_utc(b.validity_of_quote),
            notes=b.notes,
            submitted_at=ensure_utc(b.submitted_at),
            created_at=ensure_utc(b.submitted_at),
            is_valid=b.is_valid,
            rank_at_submission=b.rank_at_submission,
            is_l1=(supplier_rank_map.get(b.supplier_id) == 1 and b.total_quote == (rfq_summary.current_lowest_bid or 0)),
            triggered_extension=(b.id in extension_bid_ids)
        )
        bid_responses.append(b_resp)

    # Extensions
    extensions = [
        AuctionExtensionResponse.model_validate(ext)
        for ext in rfq.extensions
    ]

    # Activity logs (newest first)
    all_activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.rfq_id == rfq.id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )
    activities = [
        ActivityLogResponse(
            id=act.id,
            rfq_id=act.rfq_id,
            user_id=act.user_id,
            user_name=(
                act.user.supplier_profile.company_name
                if (act.user and act.user.supplier_profile and act.user.supplier_profile.company_name)
                else (act.user.full_name if act.user else "System")
            ),
            event_type=act.event_type,
            description=act.description,
            log_metadata=act.log_metadata,
            created_at=ensure_utc(act.created_at)
        )
        for act in all_activities
    ]

    return AuctionDetailResponse(
        **rfq_summary.model_dump(),
        rankings=rankings,
        bids=bid_responses,
        extensions=extensions,
        activities=activities,
        remaining_seconds=remaining_secs,
        in_trigger_window=in_trigger_window,
        my_rank=my_rank,
        my_best_bid=my_best_bid
    )


@router.get("/{rfq_id}/rankings", response_model=List[SupplierRankingEntry])
def get_auction_rankings(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="Auction not found")
    rankings, _, _ = compute_supplier_rankings(rfq, db=db)
    return rankings


@router.get("/{rfq_id}/status", response_model=AuctionStatusResponse)
def get_auction_status(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="Auction not found")

    now = datetime.now(timezone.utc)
    current_status = rfq.compute_current_status(now)
    close_utc = ensure_utc(rfq.current_bid_close_time)
    remaining_secs = max(0.0, (close_utc - now).total_seconds())

    in_window = False
    window_mins = 10.0
    if rfq.auction_config:
        window_mins = rfq.auction_config.trigger_window_minutes
        in_window = (remaining_secs > 0) and (remaining_secs <= window_mins * 60.0)

    rankings, l1_name, l1_price = compute_supplier_rankings(rfq, db=db)

    return AuctionStatusResponse(
        rfq_id=rfq.id,
        status=current_status,
        current_bid_close_time=close_utc,
        forced_bid_close_time=ensure_utc(rfq.forced_bid_close_time),
        remaining_seconds=remaining_secs,
        in_trigger_window=in_window,
        trigger_window_minutes=window_mins,
        extension_count=len(rfq.extensions),
        current_lowest_bid=l1_price,
        l1_carrier_name=l1_name
    )


@router.get("/{rfq_id}/extensions", response_model=List[AuctionExtensionResponse])
def get_auction_extensions(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="Auction not found")
    return [AuctionExtensionResponse.model_validate(e) for e in rfq.extensions]


@router.get("/{rfq_id}/activities", response_model=List[ActivityLogResponse])
def get_auction_activities(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="Auction not found")
    all_activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.rfq_id == rfq.id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )
    return [
        ActivityLogResponse(
            id=act.id,
            rfq_id=act.rfq_id,
            user_id=act.user_id,
            user_name=(
                act.user.supplier_profile.company_name
                if (act.user and act.user.supplier_profile and act.user.supplier_profile.company_name)
                else (act.user.full_name if act.user else "System")
            ),
            event_type=act.event_type,
            description=act.description,
            log_metadata=act.log_metadata,
            created_at=ensure_utc(act.created_at)
        )
        for act in all_activities
    ]


@router.post("/{rfq_id}/demo-time")
async def demo_adjust_auction_time(
    rfq_id: int,
    remaining_minutes: float = Query(..., gt=0, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Testing helper: sets the remaining auction time directly into the trigger window."""
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="Auction not found")

    now = datetime.now(timezone.utc)
    new_close = now + timedelta(minutes=remaining_minutes)

    forced_utc = ensure_utc(rfq.forced_bid_close_time)
    if forced_utc <= new_close:
        rfq.forced_bid_close_time = new_close + timedelta(minutes=30)

    old_close = ensure_utc(rfq.current_bid_close_time)
    rfq.current_bid_close_time = new_close
    start_utc = ensure_utc(rfq.bid_start_time)
    if start_utc > (now - timedelta(minutes=10)):
        rfq.bid_start_time = now - timedelta(minutes=10)
    rfq.status = AuctionStatus.ACTIVE

    db.add(ActivityLog(
        rfq_id=rfq.id,
        user_id=current_user.id,
        event_type="DEMO_TIME_ADJUSTED",
        description=f"Clock adjusted for live evaluation to close in {remaining_minutes:.1f} minutes",
        log_metadata=f"New close: {new_close.strftime('%H:%M:%S UTC')}",
        created_at=now
    ))
    db.commit()

    # Broadcast via WebSocket
    await ws_manager.broadcast_to_auction(rfq.id, "AUCTION_EXTENDED", {
        "rfq_id": rfq.id,
        "new_close_time": new_close.isoformat(),
        "remaining_seconds": remaining_minutes * 60.0
    })

    return {"message": "Auction time adjusted", "new_close_time": new_close.isoformat()}
