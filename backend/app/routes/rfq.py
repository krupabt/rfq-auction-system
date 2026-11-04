import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models.user import User, UserRole
from ..models.rfq import RFQ, AuctionStatus
from ..models.auction import AuctionConfiguration
from ..models.activity import ActivityLog
from ..schemas.rfq import RFQCreate, RFQUpdate, RFQResponse
from ..services.ranking_service import compute_supplier_rankings, ensure_utc
from ..services.websocket_manager import ws_manager
from ..dependencies import get_current_user, require_buyer_or_admin

router = APIRouter(prefix="/api/rfqs", tags=["RFQs"])


def build_rfq_response(rfq: RFQ) -> RFQResponse:
    now = datetime.now(timezone.utc)
    current_status = rfq.compute_current_status(now)
    rankings, l1_name, l1_price = compute_supplier_rankings(rfq)

    # Unique suppliers count
    unique_suppliers = {b.supplier_id for b in rfq.bids if b.is_valid}

    return RFQResponse(
        id=rfq.id,
        reference_id=rfq.reference_id,
        name=rfq.name,
        description=rfq.description,
        buyer_id=rfq.buyer_id,
        buyer_name=rfq.buyer.full_name if rfq.buyer else "Unknown Buyer",
        origin=rfq.origin,
        destination=rfq.destination,
        cargo_details=rfq.cargo_details,
        pickup_service_date=ensure_utc(rfq.pickup_service_date),
        bid_start_time=ensure_utc(rfq.bid_start_time),
        original_bid_close_time=ensure_utc(rfq.original_bid_close_time),
        current_bid_close_time=ensure_utc(rfq.current_bid_close_time),
        forced_bid_close_time=ensure_utc(rfq.forced_bid_close_time),
        status=current_status,
        is_british_auction=rfq.is_british_auction,
        target_price=rfq.target_price,
        extension_count=len(rfq.extensions),
        current_lowest_bid=l1_price,
        l1_carrier_name=l1_name,
        total_bids_count=len(rfq.bids),
        total_suppliers_count=len(unique_suppliers),
        created_at=ensure_utc(rfq.created_at),
        updated_at=ensure_utc(rfq.updated_at),
        auction_config=rfq.auction_config
    )


@router.post("", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
async def create_rfq(
    rfq_in: RFQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_buyer_or_admin)
):
    now = datetime.now(timezone.utc)
    # Check start time not excessively in past
    start_utc = ensure_utc(rfq_in.bid_start_time)
    close_utc = ensure_utc(rfq_in.bid_close_time)
    forced_utc = ensure_utc(rfq_in.forced_bid_close_time)

    # Generate unique reference ID
    random_code = uuid.uuid4().hex[:6].upper()
    reference_id = f"RFQ-{datetime.now().year}-{random_code}"

    # Determine initial status
    initial_status = AuctionStatus.SCHEDULED
    if now >= start_utc:
        initial_status = AuctionStatus.ACTIVE

    new_rfq = RFQ(
        reference_id=reference_id,
        name=rfq_in.name,
        description=rfq_in.description,
        buyer_id=current_user.id,
        origin=rfq_in.origin,
        destination=rfq_in.destination,
        cargo_details=rfq_in.cargo_details,
        pickup_service_date=ensure_utc(rfq_in.pickup_service_date),
        bid_start_time=start_utc,
        original_bid_close_time=close_utc,
        current_bid_close_time=close_utc,
        forced_bid_close_time=forced_utc,
        status=initial_status,
        is_british_auction=rfq_in.is_british_auction,
        target_price=rfq_in.target_price
    )
    db.add(new_rfq)
    db.flush()

    # Create British Auction Configuration if enabled
    if rfq_in.is_british_auction:
        cfg = rfq_in.auction_config
        config_obj = AuctionConfiguration(
            rfq_id=new_rfq.id,
            trigger_window_minutes=cfg.trigger_window_minutes if cfg else 10.0,
            extension_duration_minutes=cfg.extension_duration_minutes if cfg else 5.0,
            extension_trigger_type=cfg.extension_trigger_type if cfg else "L1_RANK_CHANGE"
        )
        db.add(config_obj)

    # Log RFQ creation activity
    activity = ActivityLog(
        rfq_id=new_rfq.id,
        user_id=current_user.id,
        event_type="RFQ_CREATED",
        description=f"RFQ '{new_rfq.name}' created with British Auction enabled.",
        log_metadata=(
            f"Reference: {new_rfq.reference_id}, Close: {close_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}, "
            f"Forced Close: {forced_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ),
        created_at=now
    )
    db.add(activity)

    db.commit()
    db.refresh(new_rfq)

    resp = build_rfq_response(new_rfq)

    # Broadcast to global clients
    await ws_manager.broadcast_global("RFQ_CREATED", resp.model_dump(mode="json"))
    return resp


@router.get("", response_model=List[RFQResponse])
def list_rfqs(
    search: Optional[str] = Query(None, description="Search by name, ID or port"),
    status_filter: Optional[str] = Query(None, description="SCHEDULED, ACTIVE, CLOSED, FORCE_CLOSED"),
    my_rfqs_only: bool = Query(False, description="Filter only RFQs created by current buyer"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(RFQ)

    # If supplier or buyer requesting own RFQs
    if my_rfqs_only and current_user.role == UserRole.BUYER:
        query = query.filter(RFQ.buyer_id == current_user.id)

    rfqs = query.order_by(desc(RFQ.created_at)).all()
    now = datetime.now(timezone.utc)

    results = []
    for rfq in rfqs:
        resp = build_rfq_response(rfq)
        # Apply filters
        if status_filter and resp.status.value.upper() != status_filter.upper():
            continue
        if search:
            q_term = search.lower()
            if not (
                q_term in resp.name.lower() or
                q_term in resp.reference_id.lower() or
                q_term in resp.origin.lower() or
                q_term in resp.destination.lower()
            ):
                continue
        results.append(resp)

    return results


@router.get("/{rfq_id}", response_model=RFQResponse)
def get_rfq(rfq_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return build_rfq_response(rfq)


@router.put("/{rfq_id}", response_model=RFQResponse)
def update_rfq(
    rfq_id: int,
    rfq_update: RFQUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_buyer_or_admin)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if current_user.role != UserRole.ADMIN and rfq.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this RFQ")

    for field, val in rfq_update.model_dump(exclude_unset=True).items():
        setattr(rfq, field, val)

    db.commit()
    db.refresh(rfq)
    return build_rfq_response(rfq)


@router.delete("/{rfq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rfq(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_buyer_or_admin)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if current_user.role != UserRole.ADMIN and rfq.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this RFQ")

    db.delete(rfq)
    db.commit()
    return None
