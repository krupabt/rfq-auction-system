import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User, Supplier, UserRole
from app.models.rfq import RFQ, AuctionStatus
from app.models.auction import AuctionConfiguration, ExtensionTriggerType
from app.models.bid import Bid
from app.schemas.bid import BidCreate
from app.schemas.rfq import RFQCreate
from app.services.auction_service import process_bid_submission
from app.services.ranking_service import compute_supplier_rankings, ensure_utc
from fastapi import HTTPException


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def setup_test_users(db):
    buyer = User(
        full_name="Test Buyer",
        email="buyer@test.com",
        hashed_password="hash",
        role=UserRole.BUYER
    )
    db.add(buyer)

    # 3 Suppliers
    supp_users = []
    suppliers = []
    for i in range(1, 4):
        u = User(
            full_name=f"Supplier User {i}",
            email=f"supp{i}@test.com",
            hashed_password="hash",
            role=UserRole.SUPPLIER
        )
        db.add(u)
        db.flush()
        s = Supplier(
            user_id=u.id,
            company_name=f"Carrier {i}",
            contact_person=f"Contact {i}"
        )
        db.add(s)
        supp_users.append(u)
        suppliers.append(s)

    db.commit()
    return buyer, supp_users, suppliers


def create_test_rfq(
    db,
    buyer,
    trigger_type=ExtensionTriggerType.L1_RANK_CHANGE,
    trigger_window=10.0,
    extension_duration=5.0,
    close_in_minutes=15.0,
    forced_close_in_minutes=45.0
):
    now = datetime.now(timezone.utc)
    rfq = RFQ(
        reference_id="TEST-RFQ-001",
        name="Test Freight RFQ",
        buyer_id=buyer.id,
        origin="Shanghai",
        destination="Nhava Sheva",
        pickup_service_date=now + timedelta(days=7),
        bid_start_time=now - timedelta(hours=1),
        original_bid_close_time=now + timedelta(minutes=close_in_minutes),
        current_bid_close_time=now + timedelta(minutes=close_in_minutes),
        forced_bid_close_time=now + timedelta(minutes=forced_close_in_minutes),
        status=AuctionStatus.ACTIVE,
        is_british_auction=True
    )
    db.add(rfq)
    db.flush()

    config = AuctionConfiguration(
        rfq_id=rfq.id,
        trigger_window_minutes=trigger_window,
        extension_duration_minutes=extension_duration,
        extension_trigger_type=trigger_type
    )
    db.add(config)
    db.commit()
    db.refresh(rfq)
    return rfq


def test_quote_total_calculation_and_ranking(db_session):
    buyer, supp_users, suppliers = setup_test_users(db_session)
    rfq = create_test_rfq(db_session, buyer)
    now = datetime.now(timezone.utc)

    # Carrier 1 submits $1,000 total (700 + 200 + 100)
    b1 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=700.0,
        origin_charges=200.0,
        destination_charges=100.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=10)
    )
    bid_obj1, extended1, _, meta1 = process_bid_submission(db_session, rfq.id, supp_users[0], b1, now)
    assert bid_obj1.total_quote == 1000.0
    assert meta1["new_rank"] == 1
    assert meta1["is_l1"] is True

    # Carrier 2 submits $900 total (600 + 200 + 100)
    b2 = BidCreate(
        carrier_name="Carrier 2",
        freight_charges=600.0,
        origin_charges=200.0,
        destination_charges=100.0,
        transit_time=14,
        validity_of_quote=now + timedelta(days=10)
    )
    bid_obj2, extended2, _, meta2 = process_bid_submission(db_session, rfq.id, supp_users[1], b2, now)
    assert bid_obj2.total_quote == 900.0
    assert meta2["new_rank"] == 1
    assert meta2["is_l1"] is True

    # Verify Leaderboard
    rankings, l1_name, l1_price = compute_supplier_rankings(rfq)
    assert l1_name == "Carrier 2"
    assert l1_price == 900.0
    assert len(rankings) == 2
    assert rankings[0].carrier_name == "Carrier 2"
    assert rankings[1].carrier_name == "Carrier 1"


def test_competitive_rule_lower_own_previous_bid(db_session):
    buyer, supp_users, suppliers = setup_test_users(db_session)
    rfq = create_test_rfq(db_session, buyer)
    now = datetime.now(timezone.utc)

    # Supplier 1 places $1,000
    b1 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=700.0,
        origin_charges=200.0,
        destination_charges=100.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=10)
    )
    process_bid_submission(db_session, rfq.id, supp_users[0], b1, now)

    # Supplier 1 attempts to place $1,050 (higher than their own previous $1,000) -> MUST BE REJECTED
    b_higher = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=750.0,
        origin_charges=200.0,
        destination_charges=100.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=10)
    )
    with pytest.raises(HTTPException) as exc_info:
        process_bid_submission(db_session, rfq.id, supp_users[0], b_higher, now)
    assert "must be lower than your previous best quote" in exc_info.value.detail


def test_l1_rank_change_extension_inside_window(db_session):
    buyer, supp_users, suppliers = setup_test_users(db_session)
    rfq = create_test_rfq(db_session, buyer, trigger_type=ExtensionTriggerType.L1_RANK_CHANGE, trigger_window=10.0, extension_duration=5.0)
    now = datetime.now(timezone.utc)

    # Bid 1: Carrier 1 submits $2,000 outside window (12m before close)
    close_time = ensure_utc(rfq.current_bid_close_time)
    t1 = close_time - timedelta(minutes=12)
    b1 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=1800.0,
        origin_charges=100.0,
        destination_charges=100.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=10)
    )
    _, ext1, _, _ = process_bid_submission(db_session, rfq.id, supp_users[0], b1, t1)
    assert ext1 is False
    assert len(rfq.extensions) == 0

    # Bid 2: Carrier 2 submits higher quote $2,100 inside window (5m before close) -> Should NOT trigger L1 extension
    t2 = close_time - timedelta(minutes=5)
    b2 = BidCreate(
        carrier_name="Carrier 2",
        freight_charges=1900.0,
        origin_charges=100.0,
        destination_charges=100.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=10)
    )
    _, ext2, _, _ = process_bid_submission(db_session, rfq.id, supp_users[1], b2, t2)
    assert ext2 is False
    assert len(rfq.extensions) == 0

    # Bid 3: Carrier 3 submits $1,800 inside window -> Dethrones L1 Carrier 1 ($2,000) -> MUST EXTEND by 5m!
    t3 = close_time - timedelta(minutes=4)
    old_close = ensure_utc(rfq.current_bid_close_time)
    b3 = BidCreate(
        carrier_name="Carrier 3",
        freight_charges=1600.0,
        origin_charges=100.0,
        destination_charges=100.0,
        transit_time=14,
        validity_of_quote=now + timedelta(days=10)
    )
    _, ext3, ext_rec3, meta3 = process_bid_submission(db_session, rfq.id, supp_users[2], b3, t3)
    assert ext3 is True
    assert len(rfq.extensions) == 1
    assert ensure_utc(rfq.current_bid_close_time) == old_close + timedelta(minutes=5)
    assert "L1_RANK_CHANGE" in ext_rec3.trigger_reason


def test_any_bid_extension_inside_window(db_session):
    buyer, supp_users, suppliers = setup_test_users(db_session)
    rfq = create_test_rfq(db_session, buyer, trigger_type=ExtensionTriggerType.ANY_BID, trigger_window=10.0, extension_duration=5.0)
    now = datetime.now(timezone.utc)

    # Carrier 1 submits in last 5m
    close_time = ensure_utc(rfq.current_bid_close_time)
    t = close_time - timedelta(minutes=5)
    old_close = close_time
    b1 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=1500.0,
        origin_charges=100.0,
        destination_charges=100.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=10)
    )
    _, ext, ext_rec, _ = process_bid_submission(db_session, rfq.id, supp_users[0], b1, t)
    assert ext is True
    assert len(rfq.extensions) == 1
    assert ensure_utc(rfq.current_bid_close_time) == old_close + timedelta(minutes=5)
    assert "ANY_BID" in ext_rec.trigger_reason


def test_forced_close_ceiling_capping(db_session):
    buyer, supp_users, suppliers = setup_test_users(db_session)
    now = datetime.now(timezone.utc)
    # Close in 2m, Forced close in 3m. Extension duration 5m.
    rfq = create_test_rfq(
        db_session,
        buyer,
        trigger_type=ExtensionTriggerType.ANY_BID,
        trigger_window=5.0,
        extension_duration=5.0,
        close_in_minutes=2.0,
        forced_close_in_minutes=3.0
    )

    t = ensure_utc(rfq.current_bid_close_time) - timedelta(minutes=1)
    b1 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=1000.0,
        origin_charges=100.0,
        destination_charges=100.0,
        transit_time=10,
        validity_of_quote=now + timedelta(days=5)
    )

    _, ext, ext_rec, _ = process_bid_submission(db_session, rfq.id, supp_users[0], b1, t)
    assert ext is True
    # Must equal forced close exactly!
    assert ensure_utc(rfq.current_bid_close_time) == ensure_utc(rfq.forced_bid_close_time)
    assert "Capped at Forced Bid Close Time" in ext_rec.trigger_reason


def test_rejection_after_close(db_session):
    buyer, supp_users, suppliers = setup_test_users(db_session)
    rfq = create_test_rfq(db_session, buyer, close_in_minutes=5.0, forced_close_in_minutes=10.0)
    now = datetime.now(timezone.utc)

    post_close = ensure_utc(rfq.current_bid_close_time) + timedelta(seconds=10)
    b1 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=1000.0,
        origin_charges=100.0,
        destination_charges=100.0,
        transit_time=10,
        validity_of_quote=now + timedelta(days=5)
    )

    with pytest.raises(HTTPException) as exc_info:
        process_bid_submission(db_session, rfq.id, supp_users[0], b1, post_close)
    assert "closed" in exc_info.value.detail.lower()


def test_user_scenario_l1_rank_change_5m_window_10m_extension(db_session):
    """
    Validates user test scenario:
    - Trigger Window: 5 minutes
    - Extension Duration: 10 minutes
    - Trigger Condition: Option C - L1 Rank Change
    - Original Closing Time: 11:30 PM
    - Forced Closing Time: 12:00 AM
    - Previous L1 quote: $5,400
    - New quote: $5,150
    - New supplier becomes L1 within the final 5 minutes
    - Expected: Detects beat previous L1, extends by 10m, persists log & extension, never exceeds forced close.
    """
    buyer, supp_users, suppliers = setup_test_users(db_session)
    now = datetime(2026, 11, 3, 23, 0, 0, tzinfo=timezone.utc)
    closing_time = datetime(2026, 11, 3, 23, 30, 0, tzinfo=timezone.utc) # 11:30 PM
    forced_closing_time = datetime(2026, 11, 4, 0, 0, 0, tzinfo=timezone.utc) # 12:00 AM

    rfq = RFQ(
        reference_id="GC-RFQ-SCENARIO-C",
        name="L1 Rank Change Anti-Sniping Test",
        buyer_id=buyer.id,
        origin="Shanghai",
        destination="Nhava Sheva",
        pickup_service_date=now + timedelta(days=7),
        bid_start_time=now,
        original_bid_close_time=closing_time,
        current_bid_close_time=closing_time,
        forced_bid_close_time=forced_closing_time,
        status=AuctionStatus.ACTIVE,
        is_british_auction=True
    )
    db_session.add(rfq)
    db_session.flush()

    config = AuctionConfiguration(
        rfq_id=rfq.id,
        trigger_window_minutes=5.0,
        extension_duration_minutes=10.0,
        extension_trigger_type=ExtensionTriggerType.L1_RANK_CHANGE
    )
    db_session.add(config)

    # 1. Previous L1 quote: $5,400 by Supplier 1 placed at 11:10 PM (outside trigger window)
    t_prev = datetime(2026, 11, 3, 23, 10, 0, tzinfo=timezone.utc)
    b_prev = Bid(
        rfq_id=rfq.id,
        supplier_id=suppliers[0].id,
        carrier_name=suppliers[0].company_name,
        freight_charges=5000.0,
        origin_charges=200.0,
        destination_charges=200.0,
        total_quote=5400.0,
        transit_time=15,
        validity_of_quote=now + timedelta(days=30),
        submitted_at=t_prev,
        is_valid=True,
        rank_at_submission=1
    )
    db_session.add(b_prev)
    db_session.commit()

    # Verify Supplier 1 is currently L1 at $5,400
    rankings_before, l1_name, l1_price = compute_supplier_rankings(rfq)
    assert len(rankings_before) == 1
    assert rankings_before[0].rank == 1
    assert rankings_before[0].total_quote == 5400.0
    assert l1_price == 5400.0

    # 2. New quote: $5,150 submitted at 11:27 PM by Supplier 2 (within final 5 minutes: 11:25 PM - 11:30 PM)
    t_new = datetime(2026, 11, 3, 23, 27, 0, tzinfo=timezone.utc)
    b_new_in = BidCreate(
        carrier_name="Carrier 2",
        freight_charges=4800.0,
        origin_charges=200.0,
        destination_charges=150.0,  # Total = 5,150.0
        transit_time=14,
        validity_of_quote=now + timedelta(days=30)
    )

    new_bid, was_extended, ext_rec, meta = process_bid_submission(
        db_session, rfq.id, supp_users[1], b_new_in, t_new
    )

    # 3. Assertions matching expected behavior:
    # 1. Detect that the new quote beats the previous L1
    assert meta["new_rank"] == 1
    assert meta["is_l1"] is True
    assert meta["total_quote"] == 5150.0
    assert meta["l1_price"] == 5150.0

    # 2. Verify that the bid was submitted within the trigger window & extended
    assert was_extended is True
    assert ext_rec is not None

    # 3. Extend the current closing time by 10 minutes (11:30 PM -> 11:40 PM)
    expected_new_close = datetime(2026, 11, 3, 23, 40, 0, tzinfo=timezone.utc)
    assert ensure_utc(rfq.current_bid_close_time) == expected_new_close
    assert ext_rec.extension_duration == 10.0
    assert ensure_utc(ext_rec.new_close_time) == expected_new_close

    # 4. Save the extension event in the Auction Activity Log
    ext_logs = [a for a in rfq.activity_logs if a.event_type == "AUCTION_EXTENDED"]
    assert len(ext_logs) >= 1
    assert "Auction extended to 23:40:00 UTC" in ext_logs[0].description

    # 5. Subsequent extensions capped at forced closing time (12:00 AM)
    # Fast forward: bid submitted at 11:38 PM (within new window 11:35 PM - 11:40 PM) by Supplier 3 at $4,900
    t_ext2 = datetime(2026, 11, 3, 23, 38, 0, tzinfo=timezone.utc)
    b_ext2 = BidCreate(
        carrier_name="Carrier 3",
        freight_charges=4600.0,
        origin_charges=150.0,
        destination_charges=150.0,  # Total = 4,900.0
        transit_time=12,
        validity_of_quote=now + timedelta(days=30)
    )
    _, was_extended2, _, _ = process_bid_submission(db_session, rfq.id, supp_users[2], b_ext2, t_ext2)
    assert was_extended2 is True
    # 11:40 PM + 10m = 11:50 PM
    assert ensure_utc(rfq.current_bid_close_time) == datetime(2026, 11, 3, 23, 50, 0, tzinfo=timezone.utc)

    # Next bid at 11:48 PM by Supplier 1 at $4,700: +10m reaches exactly 12:00 AM (forced close)
    t_ext3 = datetime(2026, 11, 3, 23, 48, 0, tzinfo=timezone.utc)
    b_ext3 = BidCreate(
        carrier_name="Carrier 1",
        freight_charges=4400.0,
        origin_charges=150.0,
        destination_charges=150.0,  # Total = 4,700.0
        transit_time=12,
        validity_of_quote=now + timedelta(days=30)
    )
    _, was_extended3, ext_rec3, _ = process_bid_submission(db_session, rfq.id, supp_users[0], b_ext3, t_ext3)
    assert was_extended3 is True
    assert ensure_utc(rfq.current_bid_close_time) == forced_closing_time

    # Final bid at 11:58 PM by Supplier 2 at $4,500: +10m would be 12:10 AM, must NEVER exceed forced close (12:00 AM)
    t_ext4 = datetime(2026, 11, 3, 23, 58, 0, tzinfo=timezone.utc)
    b_ext4 = BidCreate(
        carrier_name="Carrier 2",
        freight_charges=4200.0,
        origin_charges=150.0,
        destination_charges=150.0,  # Total = 4,500.0
        transit_time=12,
        validity_of_quote=now + timedelta(days=30)
    )
    _, was_extended4, _, _ = process_bid_submission(db_session, rfq.id, supp_users[1], b_ext4, t_ext4)
    # Already at forced close ceiling, cannot extend past 12:00 AM
    assert was_extended4 is False
    assert ensure_utc(rfq.current_bid_close_time) == forced_closing_time
    assert ensure_utc(rfq.current_bid_close_time) <= ensure_utc(rfq.forced_bid_close_time)


def test_multi_supplier_distinct_rankings_and_identities(db_session):
    """
    Regression Test:
    - 3 distinct suppliers participate in British Auction.
    - Verify all 3 appear distinctly in Supplier Rankings (no collapsing to single supplier).
    - Verify L1, L2, L3 ordering by total quote amount.
    - Verify carrier name is stored separately from supplier company name.
    - Verify activity audit log records the exact authenticated supplier.
    - Verify closed auctions reject bids.
    """
    now = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
    buyer = User(full_name="Global Buyer", email="buyer_reg@test.com", hashed_password="pw", role=UserRole.BUYER)
    db_session.add(buyer)
    db_session.flush()

    # Create 3 distinct suppliers
    s1_user = User(full_name="Klaus Jensen", email="maersk_reg@test.com", hashed_password="pw", role=UserRole.SUPPLIER)
    s2_user = User(full_name="Marco Rossi", email="msc_reg@test.com", hashed_password="pw", role=UserRole.SUPPLIER)
    s3_user = User(full_name="Hans Mueller", email="hapag_reg@test.com", hashed_password="pw", role=UserRole.SUPPLIER)
    db_session.add_all([s1_user, s2_user, s3_user])
    db_session.flush()

    s1_prof = Supplier(user_id=s1_user.id, company_name="A.P. Moller - Maersk", contact_person="Klaus Jensen")
    s2_prof = Supplier(user_id=s2_user.id, company_name="MSC Mediterranean Shipping Co.", contact_person="Marco Rossi")
    s3_prof = Supplier(user_id=s3_user.id, company_name="Hapag-Lloyd AG", contact_person="Hans Mueller")
    db_session.add_all([s1_prof, s2_prof, s3_prof])
    db_session.flush()

    # Create RFQ: closes at 11:00 AM, forced close 12:00 PM
    rfq = RFQ(
        reference_id="GC-REG-001",
        name="Multi-Supplier Ocean Auction",
        buyer_id=buyer.id,
        origin="Shanghai Port",
        destination="Rotterdam Port",
        pickup_service_date=now + timedelta(days=14),
        bid_start_time=now - timedelta(hours=1),
        original_bid_close_time=now + timedelta(hours=1),
        current_bid_close_time=now + timedelta(hours=1),
        forced_bid_close_time=now + timedelta(hours=2),
        status=AuctionStatus.ACTIVE,
        is_british_auction=True
    )
    db_session.add(rfq)
    db_session.flush()

    config = AuctionConfiguration(
        rfq_id=rfq.id,
        trigger_window_minutes=10.0,
        extension_duration_minutes=5.0,
        extension_trigger_type=ExtensionTriggerType.L1_RANK_CHANGE
    )
    db_session.add(config)
    db_session.commit()

    # Step 1: Supplier 1 (Maersk) submits quote: Freight $2,000, Origin $200, Dest $200 = Total $2,400
    # Carrier fleet: "Maersk Triple-E Class"
    t1 = now + timedelta(minutes=10)
    b1_in = BidCreate(
        carrier_name="Maersk Triple-E Class",
        freight_charges=2000.0,
        origin_charges=200.0,
        destination_charges=200.0,
        transit_time=24,
        validity_of_quote=now + timedelta(days=30)
    )
    bid1, _, _, _ = process_bid_submission(db_session, rfq.id, s1_user, b1_in, t1)
    assert bid1.supplier_id == s1_prof.id
    assert bid1.carrier_name == "Maersk Triple-E Class"
    assert bid1.supplier.company_name == "A.P. Moller - Maersk"

    # Step 2: Supplier 2 (MSC) submits quote: Freight $1,800, Origin $200, Dest $200 = Total $2,200
    # Carrier fleet: "MSC Gülsün Ultra"
    t2 = now + timedelta(minutes=20)
    b2_in = BidCreate(
        carrier_name="MSC Gülsün Ultra",
        freight_charges=1800.0,
        origin_charges=200.0,
        destination_charges=200.0,
        transit_time=22,
        validity_of_quote=now + timedelta(days=30)
    )
    bid2, _, _, _ = process_bid_submission(db_session, rfq.id, s2_user, b2_in, t2)
    assert bid2.supplier_id == s2_prof.id
    assert bid2.carrier_name == "MSC Gülsün Ultra"
    assert bid2.supplier.company_name == "MSC Mediterranean Shipping Co."

    # Step 3: Supplier 3 (Hapag-Lloyd) submits quote: Freight $1,600, Origin $200, Dest $200 = Total $2,000
    # Carrier fleet: "Hapag Berlin Express"
    t3 = now + timedelta(minutes=30)
    b3_in = BidCreate(
        carrier_name="Hapag Berlin Express",
        freight_charges=1600.0,
        origin_charges=200.0,
        destination_charges=200.0,
        transit_time=20,
        validity_of_quote=now + timedelta(days=30)
    )
    bid3, _, _, _ = process_bid_submission(db_session, rfq.id, s3_user, b3_in, t3)
    assert bid3.supplier_id == s3_prof.id
    assert bid3.carrier_name == "Hapag Berlin Express"
    assert bid3.supplier.company_name == "Hapag-Lloyd AG"

    # Verification 1: ALL 3 distinct suppliers appear separately in rankings
    rankings, l1_supplier, l1_price = compute_supplier_rankings(rfq, db=db_session)
    assert len(rankings) == 3, f"Expected 3 distinct suppliers in rankings, got {len(rankings)}"

    # Verification 2: Correct L1, L2, L3 ordering by total quote amount
    assert rankings[0].rank == 1
    assert rankings[0].rank_label == "L1"
    assert rankings[0].supplier_name == "Hapag-Lloyd AG"
    assert rankings[0].carrier_name == "Hapag Berlin Express"
    assert rankings[0].total_quote == 2000.0
    assert rankings[0].freight_charges == 1600.0
    assert rankings[0].origin_charges == 200.0
    assert rankings[0].destination_charges == 200.0
    assert rankings[0].transit_time == 20

    assert rankings[1].rank == 2
    assert rankings[1].rank_label == "L2"
    assert rankings[1].supplier_name == "MSC Mediterranean Shipping Co."
    assert rankings[1].carrier_name == "MSC Gülsün Ultra"
    assert rankings[1].total_quote == 2200.0
    assert rankings[1].transit_time == 22

    assert rankings[2].rank == 3
    assert rankings[2].rank_label == "L3"
    assert rankings[2].supplier_name == "A.P. Moller - Maersk"
    assert rankings[2].carrier_name == "Maersk Triple-E Class"
    assert rankings[2].total_quote == 2400.0
    assert rankings[2].transit_time == 24

    assert l1_supplier == "Hapag-Lloyd AG"
    assert l1_price == 2000.0

    # Verification 3: Audit Trail attributes quotes to the exact authenticated supplier
    activity_logs = [a for a in rfq.activity_logs if a.event_type == "BID_SUBMITTED"]
    assert len(activity_logs) == 3
    assert s1_user.id in [a.user_id for a in activity_logs]
    assert s2_user.id in [a.user_id for a in activity_logs]
    assert s3_user.id in [a.user_id for a in activity_logs]

    # Verification 4: Supplier 1 submits lower quote ($1,900) to overtake L1
    t4 = now + timedelta(minutes=40)
    b1_re_in = BidCreate(
        carrier_name="Maersk Triple-E Class",
        freight_charges=1500.0,
        origin_charges=200.0,
        destination_charges=200.0,  # Total $1,900
        transit_time=24,
        validity_of_quote=now + timedelta(days=30)
    )
    bid1_re, _, _, _ = process_bid_submission(db_session, rfq.id, s1_user, b1_re_in, t4)
    assert bid1_re.total_quote == 1900.0

    # Rankings recalculation: Still 3 distinct suppliers, Maersk is now L1
    rankings_updated, l1_supplier_updated, l1_price_updated = compute_supplier_rankings(rfq, db=db_session)
    assert len(rankings_updated) == 3
    assert rankings_updated[0].rank_label == "L1"
    assert rankings_updated[0].supplier_name == "A.P. Moller - Maersk"
    assert rankings_updated[0].total_quote == 1900.0
    assert rankings_updated[1].rank_label == "L2"
    assert rankings_updated[1].supplier_name == "Hapag-Lloyd AG"
    assert rankings_updated[1].total_quote == 2000.0
    assert rankings_updated[2].rank_label == "L3"
    assert rankings_updated[2].supplier_name == "MSC Mediterranean Shipping Co."
    assert rankings_updated[2].total_quote == 2200.0

    # Verification 5: Closed auction rejects new bids
    # Attempt bid after closing time (11:05 AM > 11:00 AM)
    t_closed = now + timedelta(hours=1, minutes=5)
    late_bid = BidCreate(
        carrier_name="MSC Gülsün Ultra",
        freight_charges=1400.0,
        origin_charges=200.0,
        destination_charges=200.0,
        transit_time=20,
        validity_of_quote=now + timedelta(days=30)
    )
    with pytest.raises(HTTPException) as exc_info:
        process_bid_submission(db_session, rfq.id, s2_user, late_bid, t_closed)
    assert exc_info.value.status_code == 400
    assert "Auction is closed" in exc_info.value.detail

