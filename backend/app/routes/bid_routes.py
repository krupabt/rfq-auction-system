from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RFQ, Quote, AuctionActivityLog
from ..schemas import (
    QuoteCreate, QuoteResponse, BidSubmissionResult,
    LeaderboardEntry, ActivityLogResponse
)
from ..auction_engine import process_quote_submission, compute_leaderboard
from ..websocket_manager import ws_manager

router = APIRouter(prefix="/api/rfqs/{rfq_id}", tags=["Quotes & Bids"])


@router.post("/quotes", response_model=BidSubmissionResult, status_code=status.HTTP_201_CREATED)
async def submit_quote(
    rfq_id: int,
    quote_in: QuoteCreate,
    simulated_current_time: Optional[datetime] = Query(None, description="Optional override of current time for testing"),
    db: Session = Depends(get_db)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    new_quote, was_extended, ext_reason, old_close, new_close = process_quote_submission(
        db=db,
        rfq=rfq,
        quote_in=quote_in,
        current_time=simulated_current_time
    )

    now = simulated_current_time or datetime.now(timezone.utc)
    current_status = rfq.get_status(now)
    leaderboard_data, l1_carrier, l1_price = compute_leaderboard(rfq)

    # Prepare QuoteResponse
    quote_resp = QuoteResponse(
        id=new_quote.id,
        rfq_id=new_quote.rfq_id,
        carrier_name=new_quote.carrier_name,
        freight_charges=new_quote.freight_charges,
        origin_charges=new_quote.origin_charges,
        destination_charges=new_quote.destination_charges,
        total_charges=new_quote.total_charges,
        transit_days=new_quote.transit_days,
        quote_validity_date=new_quote.quote_validity_date,
        notes=new_quote.notes,
        rank_at_submission=new_quote.rank_at_submission,
        current_rank=new_quote.rank_at_submission,
        is_l1=new_quote.is_l1,
        created_at=new_quote.created_at
    )

    result = BidSubmissionResult(
        quote=quote_resp,
        rfq_extended=was_extended,
        extension_reason=ext_reason,
        old_close_time=old_close,
        new_close_time=new_close,
        extension_count=rfq.extension_count,
        current_status=current_status,
        new_rank=new_quote.rank_at_submission or 1,
        is_l1=new_quote.is_l1
    )

    # Real-time WebSocket broadcasts
    # 1. Broadcast to this RFQ's room
    await ws_manager.broadcast_rfq(rfq_id, {
        "type": "BID_PLACED",
        "data": {
            "quote": quote_resp.model_dump(mode="json"),
            "rfq_extended": was_extended,
            "extension_reason": ext_reason,
            "new_close_time": new_close.isoformat() if new_close else None,
            "old_close_time": old_close.isoformat() if old_close else None,
            "extension_count": rfq.extension_count,
            "leaderboard": leaderboard_data,
            "l1_carrier": l1_carrier,
            "l1_price": l1_price,
            "status": current_status.value
        }
    })

    # 2. Broadcast summary update to global auction listing
    await ws_manager.broadcast_global({
        "type": "RFQ_UPDATED",
        "data": {
            "rfq_id": rfq.id,
            "current_lowest_bid": l1_price,
            "l1_carrier_name": l1_carrier,
            "bid_close_time": rfq.bid_close_time.isoformat(),
            "extension_count": rfq.extension_count,
            "status": current_status.value,
            "total_quotes_count": len(rfq.quotes)
        }
    })

    return result


@router.get("/quotes", response_model=List[QuoteResponse])
def get_rfq_quotes(rfq_id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    leaderboard_data, _, _ = compute_leaderboard(rfq)
    carrier_ranks = {item["carrier_name"]: item["rank"] for item in leaderboard_data}

    # Sorted by total_charges ascending
    sorted_quotes = sorted(rfq.quotes, key=lambda q: (q.total_charges, q.created_at))
    return [
        QuoteResponse(
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
        for q in sorted_quotes
    ]


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_rfq_leaderboard(rfq_id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    leaderboard_data, _, _ = compute_leaderboard(rfq)
    return [LeaderboardEntry(**item) for item in leaderboard_data]


@router.get("/activity-logs", response_model=List[ActivityLogResponse])
def get_rfq_activity_logs(rfq_id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    logs = (
        db.query(AuctionActivityLog)
        .filter(AuctionActivityLog.rfq_id == rfq_id)
        .order_by(AuctionActivityLog.created_at.desc())
        .all()
    )
    return [ActivityLogResponse.model_validate(log) for log in logs]
