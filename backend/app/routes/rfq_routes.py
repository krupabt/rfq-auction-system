import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import RFQ, Quote, AuctionActivityLog, ExtensionTriggerType, AuctionStatus
from ..schemas import (
    RFQCreate, RFQSummaryResponse, RFQDetailResponse, LeaderboardEntry,
    QuoteResponse, ActivityLogResponse
)
from ..auction_engine import ensure_utc, compute_leaderboard
from ..websocket_manager import ws_manager

router = APIRouter(prefix="/api/rfqs", tags=["RFQs"])


def build_rfq_summary(rfq: RFQ) -> RFQSummaryResponse:
    now = datetime.now(timezone.utc)
    current_status = rfq.get_status(now)
    leaderboard, l1_carrier, l1_price = compute_leaderboard(rfq)

    # Count distinct carriers
    carriers = {q.carrier_name for q in rfq.quotes}

    return RFQSummaryResponse(
        id=rfq.id,
        reference_id=rfq.reference_id,
        name=rfq.name,
        origin=rfq.origin,
        destination=rfq.destination,
        cargo_details=rfq.cargo_details,
        service_date=rfq.service_date,
        bid_start_time=rfq.bid_start_time,
        bid_close_time=rfq.bid_close_time,
        original_bid_close_time=rfq.original_bid_close_time,
        forced_bid_close_time=rfq.forced_bid_close_time,
        trigger_window_minutes=rfq.trigger_window_minutes,
        extension_duration_minutes=rfq.extension_duration_minutes,
        extension_trigger_type=rfq.extension_trigger_type,
        status=current_status,
        extension_count=rfq.extension_count,
        target_price=rfq.target_price,
        current_lowest_bid=l1_price,
        l1_carrier_name=l1_carrier,
        total_quotes_count=len(rfq.quotes),
        total_carriers_count=len(carriers),
        created_at=rfq.created_at
    )


@router.get("", response_model=List[RFQSummaryResponse])
def list_rfqs(
    status_filter: Optional[str] = Query(None, description="Filter by status: ACTIVE, CLOSED, UPCOMING, FORCE_CLOSED"),
    db: Session = Depends(get_db)
):
    rfqs = db.query(RFQ).order_by(desc(RFQ.created_at)).all()
    summaries = [build_rfq_summary(r) for r in rfqs]
    if status_filter:
        summaries = [s for s in summaries if s.status.value.upper() == status_filter.upper()]
    return summaries


@router.post("", response_model=RFQSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_rfq(rfq_in: RFQCreate, db: Session = Depends(get_db)):
    ref_id = rfq_in.reference_id
    if not ref_id:
        ref_id = f"RFQ-{uuid.uuid4().hex[:6].upper()}"
    else:
        # Check uniqueness
        existing = db.query(RFQ).filter(RFQ.reference_id == ref_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"RFQ with Reference ID '{ref_id}' already exists."
            )

    new_rfq = RFQ(
        reference_id=ref_id,
        name=rfq_in.name,
        origin=rfq_in.origin,
        destination=rfq_in.destination,
        cargo_details=rfq_in.cargo_details,
        service_date=rfq_in.service_date,
        bid_start_time=ensure_utc(rfq_in.bid_start_time),
        bid_close_time=ensure_utc(rfq_in.bid_close_time),
        original_bid_close_time=ensure_utc(rfq_in.bid_close_time),
        forced_bid_close_time=ensure_utc(rfq_in.forced_bid_close_time),
        trigger_window_minutes=rfq_in.trigger_window_minutes,
        extension_duration_minutes=rfq_in.extension_duration_minutes,
        extension_trigger_type=rfq_in.extension_trigger_type,
        target_price=rfq_in.target_price,
        extension_count=0
    )

    db.add(new_rfq)
    db.flush()

    # Log creation activity
    activity = AuctionActivityLog(
        rfq_id=new_rfq.id,
        event_type="AUCTION_CREATED",
        description=f"British Auction created: {new_rfq.name} ({new_rfq.reference_id})",
        reason=(
            f"Configured with Trigger Window: {new_rfq.trigger_window_minutes:.0f}m, "
            f"Extension: {new_rfq.extension_duration_minutes:.0f}m, "
            f"Trigger Rule: {new_rfq.extension_trigger_type.value}, "
            f"Forced Close: {new_rfq.forced_bid_close_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
    )
    db.add(activity)
    db.commit()
    db.refresh(new_rfq)

    summary = build_rfq_summary(new_rfq)
    # Broadcast new RFQ to global watchers
    await ws_manager.broadcast_global({
        "type": "RFQ_CREATED",
        "data": summary.model_dump(mode="json")
    })

    return summary


@router.get("/{rfq_id}", response_model=RFQDetailResponse)
def get_rfq_details(rfq_id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    now = datetime.now(timezone.utc)
    summary = build_rfq_summary(rfq)
    leaderboard_data, _, _ = compute_leaderboard(rfq)

    # Check trigger window and remaining time
    close_utc = ensure_utc(rfq.bid_close_time)
    remaining_secs = max(0.0, (close_utc - now).total_seconds())
    trigger_secs = rfq.trigger_window_minutes * 60.0
    in_trigger_window = (remaining_secs > 0) and (remaining_secs <= trigger_secs)

    # Map quotes sorted by total_charges ascending
    sorted_quotes = sorted(rfq.quotes, key=lambda q: (q.total_charges, q.created_at))
    quote_responses = []

    # Map current ranks
    carrier_ranks = {item["carrier_name"]: item["rank"] for item in leaderboard_data}
    for q in sorted_quotes:
        q_resp = QuoteResponse(
            id=q.id,
            rfq_id=q.rfq_id,
            carrier_name=q.carrier_name,
            freight_charges=q.freight_charges,
            origin_charges=q.origin_charges,
            destination_charges=q.destination_charges,
            total_charges=q.total_charges,
            transit_days=q.transit_days,
            quote_validity_date=q.quote_validity_date,
            notes=q.notes,
            rank_at_submission=q.rank_at_submission,
            current_rank=carrier_ranks.get(q.carrier_name),
            is_l1=q.is_l1,
            created_at=q.created_at
        )
        quote_responses.append(q_resp)

    # Activity logs
    logs = [ActivityLogResponse.model_validate(log) for log in rfq.activity_logs]

    return RFQDetailResponse(
        **summary.model_dump(),
        quotes=quote_responses,
        leaderboard=[LeaderboardEntry(**item) for item in leaderboard_data],
        activity_logs=logs,
        in_trigger_window=in_trigger_window,
        remaining_seconds=remaining_secs
    )


@router.post("/{rfq_id}/adjust-time-for-demo")
async def adjust_auction_time_for_demo(
    rfq_id: int,
    remaining_minutes: float = Query(..., gt=0, le=120, description="Set auction to close in X minutes from now"),
    db: Session = Depends(get_db)
):
    """
    Demo/Reviewer Helper: Adjusts the bid close time so it is right within the trigger window,
    allowing instant demonstration of British Auction extensions without waiting hours!
    """
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    now = datetime.now(timezone.utc)
    new_close = now + timedelta(minutes=remaining_minutes)

    # Ensure forced close is after new_close
    if rfq.forced_bid_close_time <= new_close:
        rfq.forced_bid_close_time = new_close + timedelta(minutes=30)

    old_close = rfq.bid_close_time
    rfq.bid_close_time = new_close
    rfq.bid_start_time = min(rfq.bid_start_time, now - timedelta(minutes=10))

    log = AuctionActivityLog(
        rfq_id=rfq.id,
        event_type="DEMO_TIME_ADJUSTMENT",
        description=f"Auction timer adjusted for live demo/testing",
        reason=f"Bid close time set to {remaining_minutes:.1f} minutes from now ({new_close.strftime('%H:%M:%S UTC')}).",
        old_close_time=old_close,
        new_close_time=new_close,
        created_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(rfq)

    # Notify WebSocket clients
    await ws_manager.broadcast_rfq(rfq_id, {
        "type": "AUCTION_TIME_ADJUSTED",
        "new_close_time": new_close.isoformat(),
        "remaining_seconds": remaining_minutes * 60.0
    })

    return {"message": "Auction time adjusted successfully", "new_bid_close_time": new_close.isoformat()}
