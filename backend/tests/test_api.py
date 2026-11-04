import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User, Supplier, UserRole
from app.core.security import get_password_hash


# Use StaticPool with in-memory SQLite so all connections share the same memory instance
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    
    # 1. Test Admin
    admin = User(
        full_name="Global Procurement Admin",
        email="admin@gocomet.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now
    )
    # 2. Test Buyer
    buyer = User(
        full_name="Test Buyer",
        email="testbuyer@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.BUYER,
        is_active=True,
        created_at=now
    )
    # 3. Test Supplier
    supp_user = User(
        full_name="Test Supplier User",
        email="testsupplier@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.SUPPLIER,
        is_active=True,
        created_at=now
    )
    # 4. Inactive User (Pending Account)
    inactive_user = User(
        full_name="Pending Applicant",
        email="pending@applicant.com",
        hashed_password=get_password_hash("pending123"),
        role=UserRole.SUPPLIER,
        is_active=False,
        created_at=now
    )
    db.add_all([admin, buyer, supp_user, inactive_user])
    db.flush()

    supplier_profile = Supplier(
        user_id=supp_user.id,
        company_name="Apex Freight Lines",
        contact_person="Apex Manager"
    )
    inactive_profile = Supplier(
        user_id=inactive_user.id,
        company_name="Pending Freight LLC",
        contact_person="Pending Contact"
    )
    db.add_all([supplier_profile, inactive_profile])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_auth_login_and_me(client):
    res = client.post("/api/auth/login", json={
        "email": "testbuyer@example.com",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "BUYER"

    token = data["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "testbuyer@example.com"


def test_create_and_fetch_rfq(client):
    res = client.post("/api/auth/login", json={
        "email": "testbuyer@example.com",
        "password": "password123"
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    payload = {
        "name": "Ocean Freight: Ningbo to Hamburg",
        "description": "FCL shipment test",
        "origin": "Ningbo, China",
        "destination": "Hamburg, Germany",
        "cargo_details": "40ft Container",
        "pickup_service_date": (now + timedelta(days=10)).isoformat(),
        "bid_start_time": (now - timedelta(minutes=5)).isoformat(),
        "bid_close_time": (now + timedelta(minutes=25)).isoformat(),
        "forced_bid_close_time": (now + timedelta(minutes=60)).isoformat(),
        "is_british_auction": True,
        "auction_config": {
            "trigger_window_minutes": 10.0,
            "extension_duration_minutes": 5.0,
            "extension_trigger_type": "L1_RANK_CHANGE"
        },
        "target_price": 3000.0
    }

    create_res = client.post("/api/rfqs", json=payload, headers=headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    rfq_id = created_data["id"]
    assert created_data["name"] == payload["name"]
    assert created_data["status"] == "ACTIVE"

    # Fetch detail
    get_res = client.get(f"/api/auctions/{rfq_id}", headers=headers)
    assert get_res.status_code == 200
    details = get_res.json()
    assert details["name"] == payload["name"]
    assert len(details["rankings"]) == 0


def test_supplier_submit_bid(client):
    buyer_res = client.post("/api/auth/login", json={
        "email": "testbuyer@example.com",
        "password": "password123"
    })
    buyer_token = buyer_res.json()["access_token"]
    now = datetime.now(timezone.utc)

    rfq_res = client.post("/api/rfqs", json={
        "name": "Live Reverse Auction Test",
        "origin": "Singapore",
        "destination": "Dubai",
        "pickup_service_date": (now + timedelta(days=5)).isoformat(),
        "bid_start_time": (now - timedelta(minutes=10)).isoformat(),
        "bid_close_time": (now + timedelta(minutes=15)).isoformat(),
        "forced_bid_close_time": (now + timedelta(minutes=45)).isoformat(),
        "is_british_auction": True,
        "auction_config": {
            "trigger_window_minutes": 10.0,
            "extension_duration_minutes": 5.0,
            "extension_trigger_type": "ANY_BID"
        }
    }, headers={"Authorization": f"Bearer {buyer_token}"})
    rfq_id = rfq_res.json()["id"]

    supp_res = client.post("/api/auth/login", json={
        "email": "testsupplier@example.com",
        "password": "password123"
    })
    supp_token = supp_res.json()["access_token"]
    supp_headers = {"Authorization": f"Bearer {supp_token}"}

    bid_res = client.post(f"/api/auctions/{rfq_id}/bids", json={
        "carrier_name": "Apex Freight Lines",
        "freight_charges": 1800.0,
        "origin_charges": 200.0,
        "destination_charges": 200.0,
        "transit_time": 12,
        "validity_of_quote": (now + timedelta(days=30)).isoformat(),
        "notes": "Direct service"
    }, headers=supp_headers)

    assert bid_res.status_code == 201
    bid_data = bid_res.json()
    assert bid_data["total_quote"] == 2200.0
    assert bid_data["rank_at_submission"] == 1


def test_login_all_three_roles(client):
    """Verify Admin, Buyer, and Supplier can all authenticate with email & password, returning their assigned role."""
    # 1. Admin login
    admin_res = client.post("/api/auth/login", json={"email": "admin@gocomet.com", "password": "admin123"})
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert admin_data["user"]["role"] == "ADMIN"
    assert "access_token" in admin_data

    # 2. Buyer login
    buyer_res = client.post("/api/auth/login", json={"email": "testbuyer@example.com", "password": "password123"})
    assert buyer_res.status_code == 200
    buyer_data = buyer_res.json()
    assert buyer_data["user"]["role"] == "BUYER"
    assert "access_token" in buyer_data

    # 3. Supplier login
    supp_res = client.post("/api/auth/login", json={"email": "testsupplier@example.com", "password": "password123"})
    assert supp_res.status_code == 200
    supp_data = supp_res.json()
    assert supp_data["user"]["role"] == "SUPPLIER"
    assert supp_data["user"]["supplier_profile"]["company_name"] == "Apex Freight Lines"


def test_invalid_credentials_rejection(client):
    """Verify that wrong password and unknown email addresses are rejected with HTTP 401."""
    # Wrong password
    res1 = client.post("/api/auth/login", json={"email": "admin@gocomet.com", "password": "wrongpassword"})
    assert res1.status_code == 401
    assert "Invalid email or password" in res1.json()["detail"]

    # Unknown email
    res2 = client.post("/api/auth/login", json={"email": "nonexistent@user.com", "password": "anypassword"})
    assert res2.status_code == 401
    assert "Invalid email or password" in res2.json()["detail"]


def test_inactive_account_rejection(client):
    """Verify that inactive or pending accounts cannot sign in and receive HTTP 403."""
    res = client.post("/api/auth/login", json={"email": "pending@applicant.com", "password": "pending123"})
    assert res.status_code == 403
    assert "pending administrator approval or inactive" in res.json()["detail"]


def test_public_registration_prohibits_admin_and_creates_pending_request(client):
    """Verify that public registration rejects ADMIN role and sets self-service requests to is_active=False."""
    # 1. Reject ADMIN registration
    admin_attempt = client.post("/api/auth/register", json={
        "full_name": "Rogue Admin",
        "email": "rogueadmin@test.com",
        "password": "secretpassword",
        "role": "ADMIN"
    })
    assert admin_attempt.status_code == 403
    assert "Administrator accounts is strictly prohibited" in admin_attempt.json()["detail"]

    # 2. Self-service Supplier Account Request
    supp_attempt = client.post("/api/auth/register", json={
        "full_name": "New Freight Partner",
        "email": "partner@freight.com",
        "password": "partnerpass123",
        "role": "SUPPLIER",
        "company_name": "Global Cargo Freight Lines",
        "phone": "+1 555-0199"
    })
    assert supp_attempt.status_code == 201
    supp_resp = supp_attempt.json()
    assert supp_resp["is_active"] is False
    assert "pending administrator review" in supp_resp["message"]

    # Verify that the newly registered user cannot log in until approved
    login_attempt = client.post("/api/auth/login", json={"email": "partner@freight.com", "password": "partnerpass123"})
    assert login_attempt.status_code == 403
    assert "pending administrator approval" in login_attempt.json()["detail"]


def test_role_based_access_control_and_unauthorized_endpoints(client):
    """Verify that role-based permissions are enforced strictly on the backend."""
    # Get tokens
    admin_token = client.post("/api/auth/login", json={"email": "admin@gocomet.com", "password": "admin123"}).json()["access_token"]
    buyer_token = client.post("/api/auth/login", json={"email": "testbuyer@example.com", "password": "password123"}).json()["access_token"]
    supp_token = client.post("/api/auth/login", json={"email": "testsupplier@example.com", "password": "password123"}).json()["access_token"]

    # 1. Supplier cannot create RFQ (Requires BUYER or ADMIN)
    supp_rfq = client.post("/api/rfqs", json={
        "name": "Unauthorized RFQ",
        "origin": "Port A",
        "destination": "Port B",
        "pickup_service_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat(),
        "bid_start_time": datetime.now(timezone.utc).isoformat(),
        "bid_close_time": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "forced_bid_close_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    }, headers={"Authorization": f"Bearer {supp_token}"})
    assert supp_rfq.status_code == 403

    # 2. Buyer cannot submit quote (Requires SUPPLIER or ADMIN)
    buyer_bid = client.post("/api/auctions/1/bids", json={
        "carrier_name": "Buyer False Carrier",
        "freight_charges": 1500.0,
        "transit_time": 10,
        "validity_of_quote": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    }, headers={"Authorization": f"Bearer {buyer_token}"})
    assert buyer_bid.status_code == 403

    # 3. Non-Admin (Buyer and Supplier) cannot access Admin User Management
    buyer_admin_access = client.get("/api/auth/admin/users", headers={"Authorization": f"Bearer {buyer_token}"})
    assert buyer_admin_access.status_code == 403

    supp_admin_access = client.get("/api/auth/admin/users", headers={"Authorization": f"Bearer {supp_token}"})
    assert supp_admin_access.status_code == 403

    # Admin CAN access Admin User Management
    admin_access = client.get("/api/auth/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_access.status_code == 200
    assert len(admin_access.json()) >= 4


def test_admin_provisioning_and_approving_accounts(client):
    """Verify that an Administrator can provision users with assigned roles and approve pending accounts."""
    admin_token = client.post("/api/auth/login", json={"email": "admin@gocomet.com", "password": "admin123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin provisions a new active Buyer
    create_buyer_res = client.post("/api/auth/admin/users", json={
        "full_name": "Corporate Procurement Director",
        "email": "director@enterprise.com",
        "password": "securepass123",
        "role": "BUYER",
        "is_active": True
    }, headers=admin_headers)
    assert create_buyer_res.status_code == 201
    assert create_buyer_res.json()["role"] == "BUYER"
    assert create_buyer_res.json()["is_active"] is True

    # Newly provisioned Buyer can log in immediately
    buyer_login = client.post("/api/auth/login", json={"email": "director@enterprise.com", "password": "securepass123"})
    assert buyer_login.status_code == 200
    assert buyer_login.json()["user"]["role"] == "BUYER"

    # 2. Admin approves the pending user (pending@applicant.com)
    # Find user ID
    users_list = client.get("/api/auth/admin/users", headers=admin_headers).json()
    pending_user = next(u for u in users_list if u["email"] == "pending@applicant.com")
    assert pending_user["is_active"] is False

    # Approve & activate
    approve_res = client.patch(f"/api/auth/admin/users/{pending_user['id']}/status", json={"is_active": True}, headers=admin_headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["is_active"] is True

    # Previously rejected user can now log in successfully!
    now_active_login = client.post("/api/auth/login", json={"email": "pending@applicant.com", "password": "pending123"})
    assert now_active_login.status_code == 200
    assert now_active_login.json()["user"]["is_active"] is True
    assert now_active_login.json()["user"]["role"] == "SUPPLIER"
