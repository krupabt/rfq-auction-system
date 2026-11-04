from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .models import RFQ, Quote, AuctionActivityLog, ExtensionTriggerType, AuctionStatus
from .schemas import QuoteCreate


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is timezone-aware and in UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_leaderboard(rfq: RFQ) -> Tuple[List[Dict], Optional[str], Optional[float]]:
    """
    Computes current ranking based on the lowest total charges submitted by each carrier.
    Returns: (leaderboard_list, l1_carrier_name, l1_price)
    """
    carrier_best: Dict[str, Quote] = {}
    carrier_quote_counts: Dict[str, int] = {}

    for q in rfq.quotes:
        c_name = q.carrier_name
        carrier_quote_counts[c_name] = carrier_quote_counts.get(c_name, 0) + 1
        if c_name not in carrier_best or q.total_charges < carrier_best[c_name].total_charges:
            carrier_best[c_name] = q

    sorted_quotes = sorted(
        carrier_best.values(),
        key=lambda x: (x.total_charges, ensure_utc(x.created_at))
    )

    leaderboard = []
    l1_carrier = None
    l1_price = None

    for idx, q in enumerate(sorted_quotes, start=1):
        is_l1 = (idx == 1)
        if is_l1:
            l1_carrier = q.carrier_name
            l1_price = q.total_charges

        leaderboard.append({
            "rank": idx,
            "carrier_name": q.carrier_name,
            "best_quote_id": q.id,
            "freight_charges": q.freight_charges,
            "origin_charges": q.origin_charges,
            "destination_charges": q.destination_charges,
            "total_charges": q.total_charges,
            "transit_days": q.transit_days,
            "quote_validity_date": ensure_utc(q.quote_validity_date),
            "quote_count": carrier_quote_counts.get(q.carrier_name, 1),
            "last_bid_time": ensure_utc(q.created_at),
            "is_l1": is_l1,
        })

    return leaderboard, l1_carrier, l1_price


def process_quote_submission(
    db: Session,
    rfq: RFQ,
    quote_in: QuoteCreate,
    current_time: Optional[datetime] = None
) -> Tuple[Quote, bool, Optional[str], Optional[datetime], Optional[datetime]]:
    """
    Validates and submits a quote under British Auction rules.
    Calculates trigger window, checks extension rules, updates close time if applicable,
    and creates audit logs.
    
    Returns:
        (new_quote, was_extended, extension_reason, old_close_time, new_close_time)
    """
    now = ensure_utc(current_time) if current_time else datetime.now(timezone.utc)
    bid_start = ensure_utc(rfq.bid_start_time)
    bid_close = ensure_utc(rfq.bid_close_time)
    forced_close = ensure_utc(rfq.forced_bid_close_time)

    # 1. Validation of Auction Timing
    if now < bid_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auction has not started yet. Starts at {bid_start.isoformat()}."
        )

    if now >= forced_close:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auction is force-closed. Hard limit reached at {forced_close.isoformat()}."
        )

    if now >= bid_close:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Auction is closed. Closed at {bid_close.isoformat()}."
        )

    total_charges = round(
        quote_in.freight_charges + quote_in.origin_charges + quote_in.destination_charges,
        2
    )

    # 2. Compute rankings BEFORE this quote
    old_leaderboard, old_l1_carrier, old_l1_price = compute_leaderboard(rfq)
    old_carrier_ranks = {entry["carrier_name"]: entry["rank"] for entry in old_leaderboard}

    # 3. Trigger Window Check (X minutes before current bid_close_time)
    trigger_window_delta = timedelta(minutes=rfq.trigger_window_minutes)
    trigger_start_time = bid_close - trigger_window_delta
    is_in_trigger_window = (now >= trigger_start_time) and (now <= bid_close)

    # 4. Predict ranking AFTER this quote
    simulated_best_prices: Dict[str, float] = {}
    for entry in old_leaderboard:
        simulated_best_prices[entry["carrier_name"]] = entry["total_charges"]

    curr_best = simulated_best_prices.get(quote_in.carrier_name, float("inf"))
    simulated_best_prices[quote_in.carrier_name] = min(curr_best, total_charges)

    new_sorted = sorted(simulated_best_prices.items(), key=lambda item: item[1])
    new_carrier_ranks = {carrier: rank for rank, (carrier, _) in enumerate(new_sorted, start=1)}
    new_l1_carrier = new_sorted[0][0] if new_sorted else quote_in.carrier_name
    new_rank = new_carrier_ranks.get(quote_in.carrier_name, 1)

    # Detect rank change
    rank_changed = False
    if quote_in.carrier_name not in old_carrier_ranks:
        rank_changed = True
    elif old_carrier_ranks.get(quote_in.carrier_name) != new_rank:
        rank_changed = True
    else:
        for c, r in new_carrier_ranks.items():
            if old_carrier_ranks.get(c) != r:
                rank_changed = True
                break

    l1_changed = (new_l1_carrier != old_l1_carrier)

    # 5. Evaluate British Auction Extension Trigger Condition
    should_extend = False
    trigger_reason: Optional[str] = None

    if is_in_trigger_window:
        if rfq.extension_trigger_type == ExtensionTriggerType.ANY_BID:
            should_extend = True
            trigger_reason = (
                f"Rule 'ANY_BID': New quote of ${total_charges:,.2f} placed by '{quote_in.carrier_name}' "
                f"within the {rfq.trigger_window_minutes:.0f}m trigger window."
            )
        elif rfq.extension_trigger_type == ExtensionTriggerType.ANY_RANK_CHANGE:
            if rank_changed:
                should_extend = True
                old_rk = old_carrier_ranks.get(quote_in.carrier_name, "Unranked")
                trigger_reason = (
                    f"Rule 'ANY_RANK_CHANGE': Ranking changed from {old_rk} to Rank {new_rank} "
                    f"by '{quote_in.carrier_name}' (${total_charges:,.2f}) within the {rfq.trigger_window_minutes:.0f}m trigger window."
                )
        elif rfq.extension_trigger_type == ExtensionTriggerType.L1_RANK_CHANGE:
            if l1_changed:
                should_extend = True
                trigger_reason = (
                    f"Rule 'L1_RANK_CHANGE': Lowest Bidder (L1) shifted from '{old_l1_carrier or 'None'}' "
                    f"to '{new_l1_carrier}' with quote ${total_charges:,.2f} within the {rfq.trigger_window_minutes:.0f}m trigger window."
                )

    # 6. Apply Extension & Forced Bid Close Rule
    was_extended = False
    old_close_time = bid_close
    new_close_time = None
    extension_log_reason = None

    if should_extend:
        extension_delta = timedelta(minutes=rfq.extension_duration_minutes)
        proposed_close = bid_close + extension_delta

        # Rule: The auction must never extend beyond the Forced Bid Close Time
        if proposed_close > forced_close:
            effective_close = forced_close
        else:
            effective_close = proposed_close

        if effective_close > bid_close:
            rfq.bid_close_time = effective_close
            rfq.extension_count += 1
            was_extended = True
            new_close_time = effective_close

            capped_note = " (Capped at Forced Bid Close Time)" if effective_close == forced_close else ""
            extension_log_reason = (
                f"{trigger_reason} Auction extended by {rfq.extension_duration_minutes:.0f}m "
                f"from {old_close_time.strftime('%H:%M:%S UTC')} to {effective_close.strftime('%H:%M:%S UTC')}{capped_note}."
            )
        else:
            extension_log_reason = (
                f"{trigger_reason} However, auction has reached the Forced Bid Close Time ceiling "
                f"({forced_close.strftime('%H:%M:%S UTC')}) and cannot be extended further."
            )

    # 7. Persist New Quote
    new_quote = Quote(
        rfq_id=rfq.id,
        carrier_name=quote_in.carrier_name,
        freight_charges=quote_in.freight_charges,
        origin_charges=quote_in.origin_charges,
        destination_charges=quote_in.destination_charges,
        total_charges=total_charges,
        transit_days=quote_in.transit_days,
        quote_validity_date=ensure_utc(quote_in.quote_validity_date),
        notes=quote_in.notes,
        rank_at_submission=new_rank,
        is_l1=(new_rank == 1),
        created_at=now
    )
    db.add(new_quote)
    db.flush()

    # Update is_l1 flags on older quotes for this RFQ
    for q in rfq.quotes:
        if q.id != new_quote.id:
            q.is_l1 = (q.carrier_name == new_l1_carrier and q.total_charges == simulated_best_prices.get(new_l1_carrier))

    # 8. Activity Logs
    bid_log = AuctionActivityLog(
        rfq_id=rfq.id,
        event_type="BID_SUBMITTED",
        carrier_name=quote_in.carrier_name,
        description=f"Quote of ${total_charges:,.2f} submitted by {quote_in.carrier_name} (Rank: {new_rank})",
        reason=f"Freight: ${quote_in.freight_charges:,.2f}, Origin: ${quote_in.origin_charges:,.2f}, Destination: ${quote_in.destination_charges:,.2f}",
        created_at=now
    )
    db.add(bid_log)

    if should_extend and extension_log_reason:
        ext_log = AuctionActivityLog(
            rfq_id=rfq.id,
            event_type="EXTENSION_TRIGGERED" if was_extended else "EXTENSION_CAPPED",
            carrier_name=quote_in.carrier_name,
            description=f"Time extension triggered for {rfq.reference_id}" if was_extended else "Extension reached hard cap",
            reason=extension_log_reason,
            old_close_time=old_close_time,
            new_close_time=new_close_time,
            created_at=now
        )
        db.add(ext_log)

    db.commit()
    db.refresh(new_quote)
    db.refresh(rfq)

    return new_quote, was_extended, extension_log_reason, old_close_time, new_close_time
