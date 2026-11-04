from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.rfq import RFQ, AuctionStatus
from ..models.bid import Bid
from ..models.auction import AuctionConfiguration, AuctionExtension, ExtensionTriggerType
from ..models.activity import ActivityLog
from ..models.user import User, Supplier
from ..schemas.bid import BidCreate
from .ranking_service import compute_supplier_rankings, ensure_utc


def process_bid_submission(
    db: Session,
    rfq_id: int,
    supplier_user: User,
    bid_in: BidCreate,
    current_time: Optional[datetime] = None
) -> Tuple[Bid, bool, Optional[AuctionExtension], Dict[str, Any]]:
    """
    Core British Auction Engine:
    Processes quote submission, calculates supplier rankings, evaluates trigger window & conditions,
    handles dynamic time extensions capped at forced close time, and records full audit logs.
    """
    now = ensure_utc(current_time) if current_time else datetime.now(timezone.utc)

    # 1. Fetch RFQ & Supplier Profile with row lock
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).with_for_update().first()
    if not rfq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RFQ not found")

    supplier = supplier_user.supplier_profile
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have an active supplier profile"
        )

    # 2. Timing and Status Validation
    bid_start = ensure_utc(rfq.bid_start_time)
    bid_close = ensure_utc(rfq.current_bid_close_time)
    forced_close = ensure_utc(rfq.forced_bid_close_time)

    if now < bid_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auction has not started yet. Starts at {bid_start.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )

    if now >= forced_close:
        rfq.status = AuctionStatus.FORCE_CLOSED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auction is force-closed. Hard limit reached at {forced_close.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )

    if now >= bid_close:
        rfq.status = AuctionStatus.CLOSED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auction is closed. Closed at {bid_close.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )

    total_quote = round(
        bid_in.freight_charges + bid_in.origin_charges + bid_in.destination_charges,
        2
    )

    if total_quote <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total quote must be greater than zero."
        )

    # 3. Rule: Supplier's new quote must be strictly lower than their own previous best quote
    previous_supplier_bids = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq.id, Bid.supplier_id == supplier.id, Bid.is_valid == True)
        .all()
    )
    if previous_supplier_bids:
        lowest_previous = min(b.total_quote for b in previous_supplier_bids)
        if total_quote >= lowest_previous:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Competitive Rule: Your new quote (${total_quote:,.2f}) must be lower than "
                    f"your previous best quote (${lowest_previous:,.2f})."
                )
            )

    # 4. Compute Rankings BEFORE this new bid
    old_rankings, old_l1_supplier_name, old_l1_price = compute_supplier_rankings(rfq, db=db)
    old_supplier_ranks = {entry.supplier_id: entry.rank for entry in old_rankings}
    old_l1_supplier_id = old_rankings[0].supplier_id if old_rankings else None

    # 5. Check Trigger Window (X minutes before current_bid_close_time)
    config = rfq.auction_config
    if not config:
        config = db.query(AuctionConfiguration).filter(AuctionConfiguration.rfq_id == rfq.id).first()

    is_in_trigger_window = False
    trigger_window_mins = 10.0
    extension_duration_mins = 5.0
    trigger_type = ExtensionTriggerType.L1_RANK_CHANGE

    if rfq.is_british_auction and config:
        trigger_window_mins = float(config.trigger_window_minutes)
        extension_duration_mins = float(config.extension_duration_minutes)
        trigger_type = config.extension_trigger_type

        trigger_start_time = bid_close - timedelta(minutes=trigger_window_mins)
        is_in_trigger_window = (now >= trigger_start_time) and (now <= bid_close)

    # 6. Predict Rankings AFTER this bid
    simulated_supplier_best: Dict[int, float] = {}
    for entry in old_rankings:
        simulated_supplier_best[entry.supplier_id] = entry.total_quote

    # Update with this supplier's new bid
    simulated_supplier_best[supplier.id] = total_quote
    new_sorted = sorted(simulated_supplier_best.items(), key=lambda x: x[1])
    new_supplier_ranks = {s_id: rank for rank, (s_id, _) in enumerate(new_sorted, start=1)}
    new_l1_supplier_id = new_sorted[0][0] if new_sorted else supplier.id
    new_rank = new_supplier_ranks.get(supplier.id, 1)

    # Detect rank shifts
    rank_changed = False
    if supplier.id not in old_supplier_ranks:
        rank_changed = True
    elif old_supplier_ranks.get(supplier.id) != new_rank:
        rank_changed = True
    else:
        for s_id, rk in new_supplier_ranks.items():
            if old_supplier_ranks.get(s_id) != rk:
                rank_changed = True
                break

    l1_changed = False
    if old_l1_supplier_id is None:
        l1_changed = True
    elif new_l1_supplier_id != old_l1_supplier_id:
        l1_changed = True
    elif new_rank == 1 and old_l1_price is not None and total_quote < old_l1_price:
        l1_changed = True

    # 7. Evaluate British Auction Extension Condition
    should_extend = False
    trigger_reason: Optional[str] = None
    trigger_type_str = str(trigger_type.value if hasattr(trigger_type, "value") else trigger_type)

    if rfq.is_british_auction and is_in_trigger_window:
        if trigger_type_str == "ANY_BID":
            should_extend = True
            trigger_reason = (
                f"Trigger Rule 'ANY_BID' (Option A): Quote of ${total_quote:,.2f} submitted by '{supplier.company_name}' "
                f"within the final {trigger_window_mins:.0f}m trigger window."
            )
        elif trigger_type_str == "ANY_RANK_CHANGE":
            if rank_changed:
                should_extend = True
                prev_rk = old_supplier_ranks.get(supplier.id, "Unranked")
                trigger_reason = (
                    f"Trigger Rule 'ANY_RANK_CHANGE' (Option B): Supplier '{supplier.company_name}' changed from "
                    f"Rank #{prev_rk} to Rank #{new_rank} (${total_quote:,.2f}) within the {trigger_window_mins:.0f}m trigger window."
                )
        elif trigger_type_str == "L1_RANK_CHANGE":
            if l1_changed and new_rank == 1:
                should_extend = True
                prev_desc = f"${old_l1_price:,.2f}" if old_l1_price is not None else "None"
                trigger_reason = (
                    f"Trigger Rule 'L1_RANK_CHANGE' (Option C): '{supplier.company_name}' became new Lowest Bidder (L1) "
                    f"with quote ${total_quote:,.2f} (beating previous L1 {prev_desc}) within the final {trigger_window_mins:.0f}m trigger window."
                )

    # 8. Create and Persist the New Bid
    new_bid = Bid(
        rfq_id=rfq.id,
        supplier_id=supplier.id,
        carrier_name=bid_in.carrier_name,
        freight_charges=bid_in.freight_charges,
        origin_charges=bid_in.origin_charges,
        destination_charges=bid_in.destination_charges,
        total_quote=total_quote,
        transit_time=bid_in.transit_time,
        validity_of_quote=ensure_utc(bid_in.validity_of_quote),
        notes=bid_in.notes,
        submitted_at=now,
        is_valid=True,
        rank_at_submission=new_rank
    )
    db.add(new_bid)
    db.flush()

    # 9. Apply Extension (if triggered)
    was_extended = False
    extension_record: Optional[AuctionExtension] = None
    old_close = bid_close

    if should_extend and trigger_reason:
        extension_delta = timedelta(minutes=extension_duration_mins)
        proposed_new_close = bid_close + extension_delta

        # Forced Close Ceiling Rule: New Close Time = min(Previous Close Time + Y, Forced Close Time)
        if proposed_new_close > forced_close:
            effective_new_close = forced_close
        else:
            effective_new_close = proposed_new_close

        if effective_new_close > bid_close:
            rfq.current_bid_close_time = effective_new_close
            was_extended = True

            capped_note = " (Capped at Forced Bid Close Time)" if effective_new_close == forced_close else ""
            full_reason = (
                f"{trigger_reason} Auction extended by {extension_duration_mins:.0f}m "
                f"from {old_close.strftime('%H:%M:%S UTC')} to {effective_new_close.strftime('%H:%M:%S UTC')}{capped_note}."
            )

            extension_record = AuctionExtension(
                rfq_id=rfq.id,
                previous_close_time=old_close,
                new_close_time=effective_new_close,
                extension_duration=extension_duration_mins,
                trigger_reason=full_reason,
                triggering_bid_id=new_bid.id,
                created_at=now
            )
            db.add(extension_record)
        else:
            full_reason = (
                f"{trigger_reason} However, auction has reached the Forced Bid Close ceiling "
                f"({forced_close.strftime('%H:%M:%S UTC')}). Further extensions capped."
            )

    # 10. Write Activity Logs
    # Activity 1: Bid Placed
    db.add(ActivityLog(
        rfq_id=rfq.id,
        user_id=supplier_user.id,
        event_type="BID_SUBMITTED",
        description=f"Supplier '{supplier.company_name}' submitted quote of ${total_quote:,.2f} via {bid_in.carrier_name} (Rank #{new_rank})",
        log_metadata=f"Freight: ${bid_in.freight_charges}, Origin: ${bid_in.origin_charges}, Dest: ${bid_in.destination_charges}",
        created_at=now
    ))

    # Activity 2: Extension Triggered (if applicable)
    if should_extend and trigger_reason:
        db.add(ActivityLog(
            rfq_id=rfq.id,
            user_id=supplier_user.id,
            event_type="AUCTION_EXTENDED" if was_extended else "EXTENSION_CAPPED",
            description=f"Auction extended to {rfq.current_bid_close_time.strftime('%H:%M:%S UTC')}" if was_extended else "Extension reached forced close limit",
            log_metadata=extension_record.trigger_reason if extension_record else full_reason,
            created_at=now
        ))

    db.commit()
    db.refresh(new_bid)
    db.expire(rfq, ['bids', 'extensions', 'activity_logs'])
    db.refresh(rfq)

    # Recalculate final rankings
    final_rankings, final_l1_supplier, final_l1_price = compute_supplier_rankings(rfq, db=db)

    summary_metadata = {
        "new_rank": new_rank,
        "is_l1": (new_rank == 1),
        "total_quote": total_quote,
        "was_extended": was_extended,
        "old_close_time": ensure_utc(old_close).isoformat(),
        "new_close_time": ensure_utc(rfq.current_bid_close_time).isoformat(),
        "extension_reason": extension_record.trigger_reason if extension_record else None,
        "l1_supplier": final_l1_supplier,
        "l1_price": final_l1_price,
        "rankings": [r.model_dump(mode="json") for r in final_rankings]
    }

    return new_bid, was_extended, extension_record, summary_metadata
