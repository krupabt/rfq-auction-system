# Backend Guide & Setup - British Auction RFQ System

## 1. Directory Structure

The backend is built with **FastAPI**, **SQLAlchemy 2.0 ORM**, and **Pydantic v2**, structured as follows:

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py             # App settings, JWT secrets, CORS configuration
│   │   └── security.py           # Bcrypt password hashing & JWT token encoding/decoding
│   ├── models/
│   │   ├── activity.py           # ActivityLog SQLAlchemy model
│   │   ├── auction.py            # AuctionConfiguration & AuctionExtension models
│   │   ├── bid.py                # Bid SQLAlchemy model
│   │   ├── rfq.py                # RFQ model & dynamic status computation
│   │   └── user.py               # User and Supplier SQLAlchemy models
│   ├── routes/
│   │   ├── activity.py           # Activity logs endpoints
│   │   ├── auction.py            # Auction listings, detail, status, demo-time endpoints
│   │   ├── auth.py               # Sign in, registration, and user profile endpoints
│   │   ├── bid.py                # Quote submission & bid retrieval endpoints
│   │   └── rfq.py                # RFQ creation and retrieval endpoints
│   ├── schemas/
│   │   ├── activity.py           # Pydantic audit log schemas
│   │   ├── auction.py            # Auction detail, extensions, status schemas
│   │   ├── auth.py               # User registration, login, and profile schemas
│   │   ├── bid.py                # Bid submission & ranking schemas
│   │   └── rfq.py                # RFQ creation & response schemas
│   ├── services/
│   │   ├── auction_service.py    # Core British Auction Engine: validation, extensions, logs
│   │   ├── ranking_service.py    # Real-time L1/L2/L3 ranking & tie-breaker calculations
│   │   └── websocket_manager.py  # WebSocket connection manager & broadcast channels
│   ├── database.py               # SQLite connection engine & SessionLocal sessionmaker
│   ├── dependencies.py           # FastAPI dependency injection (get_db, get_current_user, RBAC)
│   ├── main.py                   # FastAPI application factory, middleware, router mounts, WS routes
│   └── seed.py                   # Initial database seeding with demo accounts and test auctions
├── tests/
│   ├── test_api.py               # API route integration tests
│   └── test_auction_engine.py    # Engine unit & regression tests (anti-sniping, forced close, multi-supplier)
├── auction.db                    # SQLite database file (auto-generated)
├── pytest.ini                    # Pytest configuration
└── requirements.txt              # Production and testing Python dependencies
```

---

## 2. Dependencies (`requirements.txt`)

The application requires **Python 3.10+** (tested on Python 3.12.5). All dependencies are listed in `backend/requirements.txt`:

```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.0
pydantic>=2.6.0
pydantic-settings>=2.0.0
pytest>=8.0.0
httpx>=0.27.0
python-dateutil>=2.8.2
pyjwt>=2.8.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.0
python-multipart>=0.0.9
```

---

## 3. Step-by-Step Setup Instructions

### Step 1: Navigate to Backend Directory
Open your terminal (PowerShell, Command Prompt, or Bash) and navigate to the `backend` folder:
```bash
cd backend
```

### Step 2: Create a Virtual Environment
It is recommended to run within an isolated virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 4: Seed the Database
The application automatically seeds necessary demo accounts and initial RFQ auctions on startup, or you can run the seed script directly:
```bash
python -c "from app.database import SessionLocal; from app.seed import seed_database; db = SessionLocal(); seed_database(db); db.close(); print('Database seeded successfully.')"
```

### Step 5: Start the FastAPI Server
Start the Uvicorn ASGI server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend server will start at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Interactive Documentation**: `http://127.0.0.1:8000/redoc`

---

## 4. REST API Endpoint Reference

| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Public | Authenticates user credentials and returns JWT bearer token. |
| `POST` | `/api/auth/register` | Public | Registers a new user and optional supplier profile. |
| `GET` | `/api/auth/me` | Authenticated | Retrieves current logged-in user profile. |
| `GET` | `/api/rfqs` | Authenticated | Lists all RFQs with filtering and pagination. |
| `POST` | `/api/rfqs` | Buyer / Admin | Creates a new RFQ with British Auction configuration. |
| `GET` | `/api/rfqs/{id}` | Authenticated | Retrieves a specific RFQ by internal ID. |
| `GET` | `/api/auctions` | Authenticated | Lists auctions with countdown timers, lowest quotes, and status. |
| `GET` | `/api/auctions/{id}` | Authenticated | Returns detailed auction state, supplier rankings, and quote history. |
| `GET` | `/api/auctions/{id}/rankings` | Authenticated | Returns real-time supplier ranking leaderboard (L1, L2, L3). |
| `GET` | `/api/auctions/{id}/status` | Authenticated | Returns remaining seconds, trigger window status, and close times. |
| `POST` | `/api/auctions/{id}/bids` | Supplier / Admin | Submits a quote through the British Auction Engine. |
| `GET` | `/api/auctions/{id}/bids` | Authenticated | Returns chronological quote history. |
| `POST` | `/api/auctions/{id}/demo-time` | Authenticated | Evaluator fast-forward utility to adjust remaining time into trigger window. |
| `GET` | `/api/activities` | Authenticated | Returns centralized audit activity logs. |

---

## 5. British Auction Engine Business Rules

The backend service [`app.services.auction_service.py`](file:///d:/gocomet-rfq-auction/backend/app/services/auction_service.py) enforces all business rules:

1. **Quote Calculation**:
   $$\text{Total Quote} = \text{Freight Charges} + \text{Origin Charges} + \text{Destination Charges}$$
2. **Competitive Bidding Rule**:
   A supplier can only submit a new quote if their new total is strictly lower than their own previous best quote:
   $$\text{New Quote} < \min(\text{Supplier's Previous Bids})$$
3. **Trigger Window Evaluation**:
   The engine checks if the bid was submitted within $X$ minutes of `current_bid_close_time`:
   $$\text{now} \ge (\text{current\_bid\_close\_time} - X \text{ minutes})$$
4. **Trigger Conditions Supported**:
   - **Option A (`ANY_BID`)**: Any valid quote submitted during the trigger window triggers an extension.
   - **Option B (`ANY_RANK_CHANGE`)**: A quote that alters any supplier's rank position triggers an extension.
   - **Option C (`L1_RANK_CHANGE`)**: An extension is triggered only if the quote takes over the overall lowest bidder (L1) position.
5. **Forced Close Ceiling Rule**:
   $$\text{New Close Time} = \min(\text{Current Close Time} + Y \text{ minutes}, \text{Forced Close Time})$$
   Extensions are strictly capped at `forced_bid_close_time`. Once this ceiling is reached or time has expired, the auction transitions to `FORCE_CLOSED` / `CLOSED` and all further bids are rejected with HTTP 400.

---

## 6. Automated Testing with Pytest

Run the comprehensive automated test suite:
```bash
pytest -v
```

Expected output:
```text
============================= test session starts =============================
tests/test_api.py::test_auth_login_and_me PASSED                         [  9%]
tests/test_api.py::test_create_and_fetch_rfq PASSED                      [ 18%]
tests/test_api.py::test_supplier_submit_bid PASSED                       [ 27%]
tests/test_auction_engine.py::test_quote_total_calculation_and_ranking PASSED [ 36%]
tests/test_auction_engine.py::test_competitive_rule_lower_own_previous_bid PASSED [ 45%]
tests/test_auction_engine.py::test_l1_rank_change_extension_inside_window PASSED [ 54%]
tests/test_auction_engine.py::test_any_bid_extension_inside_window PASSED [ 63%]
tests/test_auction_engine.py::test_forced_close_ceiling_capping PASSED   [ 72%]
tests/test_auction_engine.py::test_rejection_after_close PASSED          [ 81%]
tests/test_auction_engine.py::test_user_scenario_l1_rank_change_5m_window_10m_extension PASSED [ 90%]
tests/test_auction_engine.py::test_multi_supplier_distinct_rankings_and_identities PASSED [100%]
======================= 11 passed, 1 warning in 13.56s ========================
```
