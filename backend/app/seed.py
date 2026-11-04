from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from .models.user import User, Supplier, UserRole
from .models.rfq import RFQ, AuctionStatus
from .models.auction import AuctionConfiguration, AuctionExtension, ExtensionTriggerType
from .models.bid import Bid
from .models.activity import ActivityLog
from .core.security import get_password_hash


def ensure_demo_accounts(db: Session):
    """
    Guarantees that the 3 demo accounts exist, are active,
    and have verified passwords and linked profiles.
    """
    now = datetime.now(timezone.utc)

    # 1. Admin Demo Account
    admin = db.query(User).filter(User.email.ilike("admin@demo.com")).first()
    if not admin:
        admin = User(
            full_name="System Admin",
            email="admin@demo.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            created_at=now
        )
        db.add(admin)
    else:
        admin.full_name = "System Admin"
        admin.hashed_password = get_password_hash("admin123")
        admin.role = UserRole.ADMIN
        admin.is_active = True

    # 2. Buyer Demo Account
    buyer = db.query(User).filter(User.email.ilike("buyer@demo.com")).first()
    if not buyer:
        buyer = User(
            full_name="Procurement Buyer",
            email="buyer@demo.com",
            hashed_password=get_password_hash("buyer123"),
            role=UserRole.BUYER,
            is_active=True,
            created_at=now
        )
        db.add(buyer)
    else:
        buyer.full_name = "Procurement Buyer"
        buyer.hashed_password = get_password_hash("buyer123")
        buyer.role = UserRole.BUYER
        buyer.is_active = True

    # 3. Supplier Demo Account
    s_user = db.query(User).filter(User.email.ilike("supplier@demo.com")).first()
    if not s_user:
        s_user = User(
            full_name="Demo Supplier",
            email="supplier@demo.com",
            hashed_password=get_password_hash("supplier123"),
            role=UserRole.SUPPLIER,
            is_active=True,
            created_at=now
        )
        db.add(s_user)
        db.flush()
    else:
        s_user.full_name = "Demo Supplier"
        s_user.hashed_password = get_password_hash("supplier123")
        s_user.role = UserRole.SUPPLIER
        s_user.is_active = True

    s_prof = db.query(Supplier).filter(Supplier.user_id == s_user.id).first()
    if not s_prof:
        db.add(Supplier(
            user_id=s_user.id,
            company_name="Demo Supplier",
            contact_person="Demo Supplier",
            phone="+1 555-0199",
            address="100 Logistics Way, Demo City"
        ))
    else:
        s_prof.company_name = "Demo Supplier"

    # Purge legacy GoComet or test accounts
    legacy_users = db.query(User).filter(
        User.email.ilike("%@gocomet.com") | User.email.ilike("%@carrier.com")
    ).all()
    for lu in legacy_users:
        db.delete(lu)

    db.commit()


def seed_database(db: Session, force_reset: bool = False):
    Base.metadata.create_all(bind=engine)

    if force_reset:
        db.query(ActivityLog).delete()
        db.query(AuctionExtension).delete()
        db.query(Bid).delete()
        db.query(AuctionConfiguration).delete()
        db.query(RFQ).delete()
        db.query(Supplier).delete()
        db.query(User).delete()
        db.commit()

    ensure_demo_accounts(db)

    # Check if RFQs already exist
    if db.query(RFQ).count() > 0:
        return

    now = datetime.now(timezone.utc)

    # Fetch demo buyer and demo supplier
    buyer_user = db.query(User).filter(User.email == "buyer@demo.com").first()
    supplier_user = db.query(User).filter(User.email == "supplier@demo.com").first()
    supp_prof = db.query(Supplier).filter(Supplier.user_id == supplier_user.id).first()

    if not buyer_user or not supplier_user or not supp_prof:
        return

    # 1. Seed RFQ 1: Ocean Freight (Active British Auction - L1 Trigger)
    rfq1 = RFQ(
        reference_id="RFQ-2026-001",
        name="Ocean Freight: Shanghai Port to Nhava Sheva",
        description="2x 40' High Cube Containers of Consumer Electronics. Requires direct vessel routing, standard 14 days free demurrage.",
        buyer_id=buyer_user.id,
        origin="Shanghai Port, China (CNSHA)",
        destination="Jawaharlal Nehru Port, India (INNSA)",
        cargo_details="2x 40' HC Containers - 24,500 KG Gross Weight",
        pickup_service_date=now + timedelta(days=14),
        bid_start_time=now - timedelta(hours=2),
        original_bid_close_time=now + timedelta(minutes=18),
        current_bid_close_time=now + timedelta(minutes=18),
        forced_bid_close_time=now + timedelta(minutes=50),
        status=AuctionStatus.ACTIVE,
        is_british_auction=True,
        target_price=2600.0,
        created_at=now - timedelta(hours=2)
    )
    db.add(rfq1)
    db.flush()

    config1 = AuctionConfiguration(
        rfq_id=rfq1.id,
        trigger_window_minutes=10.0,
        extension_duration_minutes=5.0,
        extension_trigger_type=ExtensionTriggerType.L1_RANK_CHANGE
    )
    db.add(config1)

    # Initial bids for RFQ 1
    b1 = Bid(
        rfq_id=rfq1.id,
        supplier_id=supp_prof.id,
        carrier_name="MSC Mediterranean Shipping",
        freight_charges=2200.0,
        origin_charges=250.0,
        destination_charges=200.0,
        total_quote=2650.0,
        transit_time=18,
        validity_of_quote=now + timedelta(days=30),
        notes="Includes 14 days free demurrage at destination. Direct call.",
        submitted_at=now - timedelta(minutes=50),
        is_valid=True,
        rank_at_submission=1
    )
    b2 = Bid(
        rfq_id=rfq1.id,
        supplier_id=supp_prof.id,
        carrier_name="Hapag-Lloyd AG",
        freight_charges=2100.0,
        origin_charges=220.0,
        destination_charges=200.0,
        total_quote=2520.0,
        transit_time=19,
        validity_of_quote=now + timedelta(days=25),
        notes="Real-time IoT smart container temperature and location tracking included.",
        submitted_at=now - timedelta(minutes=35),
        is_valid=True,
        rank_at_submission=1
    )
    b3 = Bid(
        rfq_id=rfq1.id,
        supplier_id=supp_prof.id,
        carrier_name="A.P. Moller - Maersk",
        freight_charges=2050.0,
        origin_charges=200.0,
        destination_charges=200.0,
        total_quote=2450.0,
        transit_time=16,
        validity_of_quote=now + timedelta(days=30),
        notes="Priority terminal berthing. Eco-fuel powered vessel.",
        submitted_at=now - timedelta(minutes=20),
        is_valid=True,
        rank_at_submission=1
    )
    db.add_all([b1, b2, b3])

    # Activity Logs for RFQ 1
    db.add_all([
        ActivityLog(
            rfq_id=rfq1.id,
            user_id=buyer_user.id,
            event_type="RFQ_CREATED",
            description="British Reverse Auction created for Shanghai to Nhava Sheva route",
            log_metadata="Trigger Window: 10m, Extension: 5m, Rule: L1_RANK_CHANGE",
            created_at=now - timedelta(hours=2)
        ),
        ActivityLog(
            rfq_id=rfq1.id,
            user_id=supplier_user.id,
            event_type="BID_SUBMITTED",
            description="MSC Mediterranean Shipping placed initial quote of $2,650.00 (Rank #1)",
            created_at=now - timedelta(minutes=50)
        ),
        ActivityLog(
            rfq_id=rfq1.id,
            user_id=supplier_user.id,
            event_type="BID_SUBMITTED",
            description="Hapag-Lloyd placed quote of $2,520.00 (Rank #1 - New L1)",
            created_at=now - timedelta(minutes=35)
        ),
        ActivityLog(
            rfq_id=rfq1.id,
            user_id=supplier_user.id,
            event_type="BID_SUBMITTED",
            description="Maersk placed quote of $2,450.00 (Rank #1 - Leading L1)",
            created_at=now - timedelta(minutes=20)
        )
    ])

    # 2. Seed RFQ 2: Air Cargo Express (Inside Trigger Window - ANY_RANK_CHANGE)
    rfq2 = RFQ(
        reference_id="RFQ-2026-002",
        name="Air Freight Express: Frankfurt to Chicago O'Hare",
        description="Temperature controlled pharma cold chain shipment (2-8 C). Urgent delivery within 48 hours.",
        buyer_id=buyer_user.id,
        origin="Frankfurt Airport, Germany (FRA)",
        destination="Chicago O'Hare International, USA (ORD)",
        cargo_details="5 Pallets - Vaccines & Active Pharma Ingredients - 1,800 KG",
        pickup_service_date=now + timedelta(days=4),
        bid_start_time=now - timedelta(minutes=30),
        original_bid_close_time=now + timedelta(minutes=4),  # In trigger window
        current_bid_close_time=now + timedelta(minutes=4),
        forced_bid_close_time=now + timedelta(minutes=25),
        status=AuctionStatus.ACTIVE,
        is_british_auction=True,
        target_price=7200.0,
        created_at=now - timedelta(minutes=30)
    )
    db.add(rfq2)
    db.flush()

    config2 = AuctionConfiguration(
        rfq_id=rfq2.id,
        trigger_window_minutes=5.0,
        extension_duration_minutes=3.0,
        extension_trigger_type=ExtensionTriggerType.ANY_RANK_CHANGE
    )
    db.add(config2)

    b2_1 = Bid(
        rfq_id=rfq2.id,
        supplier_id=supp_prof.id,
        carrier_name="CMA CGM Air Cargo",
        freight_charges=6400.0,
        origin_charges=350.0,
        destination_charges=300.0,
        total_quote=7050.0,
        transit_time=2,
        validity_of_quote=now + timedelta(days=10),
        notes="Cold-chain active container Envirotainer certified.",
        submitted_at=now - timedelta(minutes=15),
        is_valid=True,
        rank_at_submission=1
    )
    db.add(b2_1)

    db.add_all([
        ActivityLog(
            rfq_id=rfq2.id,
            user_id=buyer_user.id,
            event_type="RFQ_CREATED",
            description="Urgent Air Freight British Auction created for Frankfurt to Chicago",
            log_metadata="Trigger Window: 5m, Extension: 3m, Rule: ANY_RANK_CHANGE",
            created_at=now - timedelta(minutes=30)
        ),
        ActivityLog(
            rfq_id=rfq2.id,
            user_id=supplier_user.id,
            event_type="BID_SUBMITTED",
            description="CMA CGM Air Cargo submitted initial quote of $7,050.00 (Rank #1)",
            created_at=now - timedelta(minutes=15)
        )
    ])

    # 3. Seed RFQ 3: FCL Cross-Border (Option A - ANY_BID Trigger)
    rfq3 = RFQ(
        reference_id="RFQ-2026-003",
        name="FCL 20ft: Rotterdam Port to Port of Singapore",
        description="Industrial machinery components. Low carbon fuel preferred.",
        buyer_id=buyer_user.id,
        origin="Rotterdam Port, Netherlands (NLRTM)",
        destination="Port of Singapore (SGSIN)",
        cargo_details="1x 20' Standard GP - 14,000 KG",
        pickup_service_date=now + timedelta(days=21),
        bid_start_time=now - timedelta(hours=1),
        original_bid_close_time=now + timedelta(hours=2),
        current_bid_close_time=now + timedelta(hours=2),
        forced_bid_close_time=now + timedelta(hours=4),
        status=AuctionStatus.ACTIVE,
        is_british_auction=True,
        target_price=1650.0,
        created_at=now - timedelta(hours=1)
    )
    db.add(rfq3)
    db.flush()

    config3 = AuctionConfiguration(
        rfq_id=rfq3.id,
        trigger_window_minutes=15.0,
        extension_duration_minutes=10.0,
        extension_trigger_type=ExtensionTriggerType.ANY_BID
    )
    db.add(config3)

    db.add(ActivityLog(
        rfq_id=rfq3.id,
        user_id=buyer_user.id,
        event_type="RFQ_CREATED",
        description="FCL British Auction created for Rotterdam to Singapore",
        log_metadata="Trigger Window: 15m, Extension: 10m, Rule: ANY_BID",
        created_at=now - timedelta(hours=1)
    ))

    # 4. Seed RFQ 4: Completed British Auction (for Reports & History)
    rfq4 = RFQ(
        reference_id="RFQ-2026-004",
        name="Contract Freight: Port of Los Angeles to Tokyo",
        description="Automotive spare parts. Closed contract successfully awarded to L1 bidder.",
        buyer_id=buyer_user.id,
        origin="Port of Los Angeles, USA (USLAX)",
        destination="Tokyo Port, Japan (JPTYO)",
        cargo_details="4x 40' Dry Vans - 38,000 KG",
        pickup_service_date=now - timedelta(days=2),
        bid_start_time=now - timedelta(days=3),
        original_bid_close_time=now - timedelta(days=2, hours=12),
        current_bid_close_time=now - timedelta(days=2, hours=11, minutes=50),  # Extended twice
        forced_bid_close_time=now - timedelta(days=2, hours=10),
        status=AuctionStatus.CLOSED,
        is_british_auction=True,
        target_price=5400.0,
        created_at=now - timedelta(days=3)
    )
    db.add(rfq4)
    db.flush()

    config4 = AuctionConfiguration(
        rfq_id=rfq4.id,
        trigger_window_minutes=10.0,
        extension_duration_minutes=5.0,
        extension_trigger_type=ExtensionTriggerType.L1_RANK_CHANGE
    )
    db.add(config4)

    # Completed Bids
    b4_1 = Bid(
        rfq_id=rfq4.id,
        supplier_id=supp_prof.id,
        carrier_name="MSC Mediterranean Shipping",
        freight_charges=4600.0,
        origin_charges=300.0,
        destination_charges=300.0,
        total_quote=5200.0,
        transit_time=12,
        validity_of_quote=now + timedelta(days=30),
        submitted_at=now - timedelta(days=2, hours=13),
        is_valid=True,
        rank_at_submission=1
    )
    b4_2 = Bid(
        rfq_id=rfq4.id,
        supplier_id=supp_prof.id,
        carrier_name="A.P. Moller - Maersk",
        freight_charges=4300.0,
        origin_charges=250.0,
        destination_charges=250.0,
        total_quote=4800.0,
        transit_time=11,
        validity_of_quote=now + timedelta(days=30),
        submitted_at=now - timedelta(days=2, hours=12, minutes=5),
        is_valid=True,
        rank_at_submission=1
    )
    db.add_all([b4_1, b4_2])

    ext1 = AuctionExtension(
        rfq_id=rfq4.id,
        previous_close_time=now - timedelta(days=2, hours=12),
        new_close_time=now - timedelta(days=2, hours=11, minutes=55),
        extension_duration=5.0,
        trigger_reason="Rule L1_RANK_CHANGE: Maersk dethroned MSC ($4,800 < $5,200) in trigger window.",
        triggering_bid_id=b4_2.id,
        created_at=now - timedelta(days=2, hours=12, minutes=5)
    )
    db.add(ext1)

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db, force_reset=True)
        print("Database cleanly initialized and seeded with enterprise users & auctions!")
    finally:
        db.close()
