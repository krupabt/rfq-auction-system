from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session, object_session
from ..models.rfq import RFQ
from ..models.bid import Bid
from ..schemas.bid import SupplierRankingEntry


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_supplier_rankings(rfq: RFQ, db: Optional[Session] = None) -> Tuple[List[SupplierRankingEntry], Optional[str], Optional[float]]:
    """
    Computes real-time rankings for all participating suppliers in an RFQ.
    - Each supplier's standing is determined by their single lowest total_quote.
    - Ties are broken by earlier submission time (first-come, first-served).
    - Returns: (rankings_list, l1_supplier_name, l1_price)
    """
    session = db or object_session(rfq)
    if session is not None:
        valid_bids = session.query(Bid).filter(Bid.rfq_id == rfq.id, Bid.is_valid == True).all()
    else:
        valid_bids = [b for b in rfq.bids if b.is_valid]

    # Group by supplier_id, keeping the best (lowest total_quote)
    supplier_best_map: Dict[int, Bid] = {}
    supplier_bids_count: Dict[int, int] = {}

    for bid in valid_bids:
        s_id = bid.supplier_id
        supplier_bids_count[s_id] = supplier_bids_count.get(s_id, 0) + 1

        if s_id not in supplier_best_map or bid.total_quote < supplier_best_map[s_id].total_quote:
            supplier_best_map[s_id] = bid
        elif bid.total_quote == supplier_best_map[s_id].total_quote:
            # Tie breaker: earlier submission
            if ensure_utc(bid.submitted_at) < ensure_utc(supplier_best_map[s_id].submitted_at):
                supplier_best_map[s_id] = bid

    # Sort suppliers: 1st by total_quote ascending, 2nd by submitted_at ascending
    sorted_bids = sorted(
        supplier_best_map.values(),
        key=lambda b: (b.total_quote, ensure_utc(b.submitted_at))
    )

    rankings: List[SupplierRankingEntry] = []
    l1_supplier = None
    l1_price = None

    for index, b in enumerate(sorted_bids, start=1):
        is_l1 = (index == 1)
        supplier_company = b.supplier.company_name if b.supplier else b.carrier_name
        if is_l1:
            l1_supplier = supplier_company
            l1_price = b.total_quote

        entry = SupplierRankingEntry(
            rank=index,
            rank_label=f"L{index}",
            supplier_id=b.supplier_id,
            supplier_name=supplier_company,
            company_name=supplier_company,
            carrier_name=b.carrier_name,
            best_bid_id=b.id,
            freight_charges=b.freight_charges,
            origin_charges=b.origin_charges,
            destination_charges=b.destination_charges,
            total_quote=b.total_quote,
            transit_time=b.transit_time,
            validity_of_quote=ensure_utc(b.validity_of_quote),
            total_bids_placed=supplier_bids_count.get(b.supplier_id, 1),
            last_bid_time=ensure_utc(b.submitted_at),
            last_bid_at=ensure_utc(b.submitted_at),
            is_l1=is_l1
        )
        rankings.append(entry)

    return rankings, l1_supplier, l1_price
