from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.rfq import RFQ
from ..models.bid import Bid
from ..models.user import User, UserRole
from ..schemas.bid import BidCreate, BidResponse
from ..services.auction_service import process_bid_submission
from ..services.ranking_service import compute_supplier_rankings, ensure_utc
from ..services.websocket_manager import ws_manager
from ..dependencies import get_current_user, require_supplier_or_admin

router = APIRouter(prefix="/api/auctions/{rfq_id}/bids", tags=["Bids"])


@router.post("", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
async def submit_bid(
    rfq_id: int,
    bid_in: BidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier_or_admin)
):
    # Process through the core British Auction Engine
    new_bid, was_extended, ext_record, metadata = process_bid_submission(
        db=db,
        rfq_id=rfq_id,
        supplier_user=current_user,
        bid_in=bid_in
    )

    resp = BidResponse(
        id=new_bid.id,
        rfq_id=new_bid.rfq_id,
        supplier_id=new_bid.supplier_id,
        carrier_name=new_bid.carrier_name,
        supplier_company_name=new_bid.supplier.company_name if new_bid.supplier else new_bid.carrier_name,
        freight_charges=new_bid.freight_charges,
        origin_charges=new_bid.origin_charges,
        destination_charges=new_bid.destination_charges,
        total_quote=new_bid.total_quote,
        transit_time=new_bid.transit_time,
        validity_of_quote=ensure_utc(new_bid.validity_of_quote),
        notes=new_bid.notes,
        submitted_at=ensure_utc(new_bid.submitted_at),
        is_valid=new_bid.is_valid,
        rank_at_submission=new_bid.rank_at_submission,
        is_l1=metadata["is_l1"]
    )

    # Broadcast real-time events over WebSockets
    # 1. To the specific Auction Room
    await ws_manager.broadcast_to_auction(rfq_id, "BID_SUBMITTED", {
        "bid": resp.model_dump(mode="json"),
        "was_extended": was_extended,
        "extension_reason": metadata["extension_reason"],
        "new_close_time": metadata["new_close_time"],
        "rankings": metadata["rankings"],
        "l1_supplier": metadata["l1_supplier"],
        "l1_price": metadata["l1_price"]
    })

    if was_extended:
        await ws_manager.broadcast_to_auction(rfq_id, "AUCTION_EXTENDED", {
            "rfq_id": rfq_id,
            "was_extended": True,
            "new_close_time": metadata["new_close_time"],
            "extension_reason": metadata["extension_reason"],
            "l1_supplier": metadata["l1_supplier"],
            "l1_price": metadata["l1_price"]
        })

    # 2. To the Global Dashboard
    await ws_manager.broadcast_global("DASHBOARD_UPDATE", {
        "rfq_id": rfq_id,
        "new_lowest_bid": metadata["l1_price"],
        "l1_supplier": metadata["l1_supplier"],
        "was_extended": was_extended,
        "new_close_time": metadata["new_close_time"]
    })

    return resp


@router.get("", response_model=List[BidResponse])
def get_rfq_bids(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    rankings, _, _ = compute_supplier_rankings(rfq, db=db)
    supplier_rank_map = {r.supplier_id: r.rank for r in rankings}
    extension_bid_ids = {ext.triggering_bid_id for ext in rfq.extensions if ext.triggering_bid_id}

    chronological_bids = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq.id)
        .order_by(Bid.submitted_at.desc())
        .all()
    )
    return [
        BidResponse(
            id=b.id,
            rfq_id=b.rfq_id,
            supplier_id=b.supplier_id,
            carrier_name=b.carrier_name,
            supplier_company_name=b.supplier.company_name if b.supplier else b.carrier_name,
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
            is_l1=(supplier_rank_map.get(b.supplier_id) == 1 and b.total_quote == (rankings[0].total_quote if rankings else 0)),
            triggered_extension=(b.id in extension_bid_ids)
        )
        for b in chronological_bids
    ]


@router.get("/my-bids", response_model=List[BidResponse])
def get_my_bids(
    rfq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supplier_or_admin)
):
    if not current_user.supplier_profile:
        raise HTTPException(status_code=403, detail="No supplier profile associated with this account")

    supplier_id = current_user.supplier_profile.id
    bids = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq_id, Bid.supplier_id == supplier_id)
        .order_by(Bid.submitted_at.desc())
        .all()
    )

    return [
        BidResponse(
            id=b.id,
            rfq_id=b.rfq_id,
            supplier_id=b.supplier_id,
            carrier_name=b.carrier_name,
            supplier_company_name=b.supplier.company_name if b.supplier else b.carrier_name,
            freight_charges=b.freight_charges,
            origin_charges=b.origin_charges,
            destination_charges=b.destination_charges,
            total_quote=b.total_quote,
            transit_time=b.transit_time,
            validity_of_quote=ensure_utc(b.validity_of_quote),
            notes=b.notes,
            submitted_at=ensure_utc(b.submitted_at),
            is_valid=b.is_valid,
            rank_at_submission=b.rank_at_submission,
            is_l1=False
        )
        for b in bids
    ]
