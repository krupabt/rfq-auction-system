# British Auction in Request for Quotation (RFQ) System

> **College Assignment Submission**  
> **Course / Project:** Enterprise Reverse Auction & Procurement System  
> **Deliverables Included:** HLD with Architecture Diagram, Database Schema Design with ER Diagram, Backend Source Code, Frontend Source Code.

---

## 📋 Assignment Deliverables Summary

This repository contains all four required deliverables organized cleanly:

| # | Deliverable | Location | Description |
| :- | :--- | :--- | :--- |
| **1** | **High-Level Design (HLD)** | [`docs/HLD.pdf`](docs/HLD.pdf) | Comprehensive 3-page HLD document with system architecture diagram, sequence diagram, anti-sniping extension rules, and API specifications. |
| **2** | **Database Schema Design** | [`docs/Database_Schema.pdf`](docs/Database_Schema.pdf) | Full 3-page schema specification with entity-relationship (ER) diagram, 7 normalized tables data dictionary, constraints, indexes, and relationships. |
| **3** | **Backend Code** | [`backend/`](backend/) | Python FastAPI asynchronous REST API & WebSocket server with SQLAlchemy 2.0 ORM, JWT authentication, RBAC, British Auction engine, and 17 automated tests. |
| **4** | **Frontend Code** | [`frontend/`](frontend/) | React 19 single-page application built with Vite, Tailwind CSS, Lucide icons, responsive sidebar navigation, real-time auction room, and countdown monitors. |

---

## 🌟 Key Features

1. **Procurement RFQ Management:** Buyers can create and manage Request for Quotations (RFQs) with route details, cargo specifications, and customizable British Auction rules.
2. **British Auction Anti-Sniping Engine:**
   - **Trigger Window ($X$ minutes):** Automatically monitors quotes submitted within the final $X$ minutes of closing.
   - **Extension Duration ($Y$ minutes):** Dynamically adds $Y$ minutes to the closing deadline when qualifying competitive quotes are placed.
   - **Three Extension Trigger Conditions:**
     - **Option A (`ANY_BID`):** Any valid quote in the final $X$ minutes extends the auction.
     - **Option B (`ANY_RANK_CHANGE`):** Any quote that improves any supplier's leaderboard position extends the auction.
     - **Option C (`L1_RANK_CHANGE`):** Only a new market-leading lowest quote ($L1$) extends the auction.
   - **Forced Close Hard Ceiling:** $\text{New Close Time} = \min(\text{Current Close} + Y, \;\text{Forced Bid Close Time})$. Guarantees that auctions can never be extended indefinitely.
3. **Competitive Supplier Bidding:**
   - Single Best Supplier Rule: Each supplier's lowest total quote is ranked ($L1, L2, L3, \dots$).
   - Competitive Improvement Rule: A supplier cannot submit a quote unless it strictly beats their own previous best rate.
   - Tie-breaking: Earlier submission timestamp wins ties.
4. **Real-Time WebSocket Synchronization:** Sub-second push notifications for new quotes, countdown adjustments, dynamic extension banners, and leaderboard changes.
5. **Role-Based Access Control (RBAC):** Dedicated views and permissions for **Admin**, **Buyer**, and **Supplier** roles.
6. **Student-Friendly Admin User Management:** Simple interface to view users, add new users, assign roles (Admin, Buyer, Supplier), and activate/deactivate accounts.

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | React | 19.x | Component-based interactive single-page application |
| | Vite | 6.x | High-speed frontend build tool and dev server |
| | Tailwind CSS | 3.4.x | Utility-first clean responsive styling |
| | React Router DOM | 7.x | Client-side routing and protected role routes |
| | Axios | 1.7.x | REST API client with JWT bearer interceptors |
| | Native WebSockets | HTML5 | Real-time live bidding and countdown events |
| **Backend** | Python | 3.12+ | Core backend runtime |
| | FastAPI | 0.115.x | High-performance asynchronous web framework |
| | Uvicorn | 0.34.x | Lightning-fast ASGI production server |
| | SQLAlchemy | 2.0.x | Relational Object-Relational Mapping (ORM) |
| | Pydantic | 2.x | Data validation and JSON schema serialization |
| | python-jose / bcrypt | Latest | Stateless JWT authentication & password hashing |
| | Pytest | 8.x | Automated unit and integration test suite |
| **Database** | SQLite 3 | Embedded | ACID-compliant relational persistence (`auction.db`) |
| **Docs** | ReportLab & Matplotlib | Latest | Vector diagram & publication-quality PDF generation |

---

## 📁 Repository Directory Structure

```text
gocomet-rfq-auction/
├── .gitignore                      # Git ignore rules for venvs, node_modules, cache & DB
├── README.md                       # Project documentation & execution guide
├── backend/                        # Backend Application (FastAPI + SQLAlchemy)
│   ├── app/
│   │   ├── core/                   # Security, JWT tokens, config & DB session setup
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/                 # 7 SQLAlchemy Relational Data Models
│   │   │   ├── activity.py         # ActivityLog entity
│   │   │   ├── auction.py          # AuctionConfiguration & AuctionExtension
│   │   │   ├── bid.py              # Bid quote entity
│   │   │   ├── rfq.py              # RFQ procurement entity
│   │   │   └── user.py             # User & Supplier profile entities
│   │   ├── routes/                 # FastAPI REST Endpoints & Routers
│   │   │   ├── activity.py         # /api/activity audit trail
│   │   │   ├── admin.py            # /api/admin user management (view, add, role, toggle)
│   │   │   ├── auction.py          # /api/auctions auction state & countdowns
│   │   │   ├── auth.py             # /api/auth login, registration & profile
│   │   │   ├── bid.py              # /api/auctions/{id}/bids quote submission
│   │   │   ├── dashboard.py        # /api/dashboard statistics & metrics
│   │   │   ├── reports.py          # /api/reports analytics
│   │   │   └── rfq.py              # /api/rfqs RFQ creation & search
│   │   ├── schemas/                # Pydantic v2 Request & Response Schemas
│   │   ├── services/               # Core Domain Logic
│   │   │   ├── auction_service.py  # British Auction extension & anti-sniping logic
│   │   │   └── ranking_service.py  # Supplier ranking & leaderboard logic
│   │   ├── websocket/              # Real-Time WebSocket Connection Manager
│   │   │   └── manager.py
│   │   ├── main.py                 # FastAPI application entrypoint & middleware
│   │   └── seed.py                 # Initial database seeding script
│   ├── tests/                      # Automated Pytest Test Suite
│   │   ├── conftest.py             # Test fixtures & test DB setup
│   │   ├── test_api.py             # REST API endpoint tests
│   │   └── test_auction_engine.py  # British auction rule unit tests (A, B, C, limits)
│   ├── requirements.txt            # Python dependencies
│   └── auction.db                  # Local SQLite database file
├── frontend/                       # Frontend Client Application (React 19 + Vite)
│   ├── public/                     # Static assets
│   ├── src/
│   │   ├── components/             # Reusable UI components (Sidebar, Navbar, Cards)
│   │   ├── context/                # AuthContext & WebSocket live state provider
│   │   ├── pages/                  # Application views & dashboards
│   │   │   ├── AdminDashboard.jsx  # Student-level User Management UI
│   │   │   ├── AuctionDetail.jsx   # Live British Auction room & bidding console
│   │   │   ├── BuyerDashboard.jsx  # Buyer procurement overview
│   │   │   ├── CreateRFQ.jsx       # RFQ creation with British Auction rule form
│   │   │   ├── Dashboard.jsx       # Global metrics & recent auctions
│   │   │   ├── Login.jsx           # Clean authentication page
│   │   │   ├── RFQList.jsx         # RFQ listings with status filters
│   │   │   └── SupplierDashboard.jsx # Supplier quoting interface
│   │   ├── services/               # Axios API client bindings
│   │   ├── App.jsx                 # Route definitions & protected routes
│   │   └── main.jsx                # React root mount
│   ├── package.json                # Node dependencies & npm scripts
│   ├── tailwind.config.js          # Tailwind styling configuration
│   └── vite.config.js              # Vite server & build configuration
└── docs/                           # Documentation & Deliverables
    ├── HLD.pdf                     # Deliverable 1: High-Level Design PDF
    ├── Database_Schema.pdf         # Deliverable 2: Database Schema Design PDF
    ├── architecture_diagram.png    # High-res architecture diagram
    ├── workflow_diagram.png        # High-res British Auction sequence workflow
    ├── er_diagram.png              # High-res Entity-Relationship diagram
    ├── high-level-design.md        # HLD Markdown source
    ├── database-schema.md          # Database Schema Markdown source
    ├── backend-guide.md            # Backend developer guide
    ├── frontend-guide.md           # Frontend developer guide
    ├── build_pdfs.py               # Automated PDF compilation script
    └── generate_diagrams.py        # Vector diagram generator
```

---

## 🚀 Setup & Execution Guide

### Prerequisites
- **Python**: 3.12 or higher
- **Node.js**: 20.x or higher
- **npm**: 10.x or higher

---

### Step 1: Backend Setup & Launch

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. *(Optional)* Seed initial demo data:
   ```bash
   python -m app.seed
   ```

5. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

- **Backend API URL:** `http://127.0.0.1:8000`
- **Interactive Swagger API Docs:** `http://127.0.0.1:8000/docs`
- **Alternative ReDoc Docs:** `http://127.0.0.1:8000/redoc`

---

### Step 2: Frontend Setup & Launch

1. Open a second terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

- **Frontend Application URL:** `http://localhost:5173`

---

## 👥 Demo User Accounts for Testing

The system comes pre-seeded with simple, intuitive demo accounts:

| Role | Email | Password | Access & Capabilities |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@demo.com` | `admin123` | Simple User Management (View Users, Add User, Assign Role, Activate/Deactivate) |
| **Procurement Buyer** | `buyer@demo.com` | `buyer123` | Create RFQs, configure British Auction rules, view live bids, monitor closings |
| **Demo Supplier** | `supplier@demo.com` | `supplier123` | View active reverse auctions, submit competitive quotes, view live ranking ($L1/L2$) |

---

## 🧪 Automated Testing

The backend includes a comprehensive automated test suite testing the British Auction algorithm and API integrity:

```bash
cd backend
python -m pytest -v
```

### Verified Test Suite (17 Passing Tests):
- ✅ `test_quote_total_calculation_and_ranking`: Verifies quote math (`freight + origin + destination`) and $L1/L2/L3$ sorting.
- ✅ `test_competitive_rule_lower_own_previous_bid`: Rejects higher or equal quotes from the same supplier.
- ✅ `test_single_best_supplier_rule`: Ensures only each supplier's best quote enters the leaderboard.
- ✅ `test_tie_breaking_earlier_timestamp`: Earlier bid wins rank when prices match.
- ✅ `test_any_bid_extension_inside_window` (Option A): Extends on any valid quote in trigger window.
- ✅ `test_any_rank_change_extension_inside_window` (Option B): Extends only when rank changes.
- ✅ `test_l1_rank_change_extension_inside_window` (Option C): Extends only when new $L1$ leader is established.
- ✅ `test_no_extension_outside_window`: Quotes placed before the trigger window do not extend.
- ✅ `test_forced_close_ceiling_capping`: Extensions strictly clamp to `forced_bid_close_time`.
- ✅ `test_rejection_after_close`: Rejects bids after auction closing deadline.
- ✅ `test_auth_login_and_me`: Validates JWT token generation, verification, and profile endpoints.
- ✅ `test_create_and_fetch_rfq`: Validates buyer RFQ publication and persistence.
- ✅ `test_supplier_submit_bid`: Validates end-to-end bid submission and real-time updates.

---

## 🔄 British Auction Anti-Sniping Logic Walkthrough

```text
[Auction Running] 
       │
       ▼
Supplier submits Quote in final X minutes?
       ├────────► NO  ──► Record bid, recalculate rankings, no extension.
       ▼
      YES
       │
Trigger Condition Satisfied? (Option A: Any Bid | Option B: Rank Shift | Option C: New L1)
       ├────────► NO  ──► Record bid, recalculate rankings, no extension.
       ▼
      YES
       │
Calculate: Proposed New Close = Current Close + Y minutes
       │
Proposed New Close > Forced Bid Close Time?
       ├────────► YES ──► Clamp New Close = Forced Bid Close Time (Hard Ceiling Reached)
       ├────────► NO  ──► Apply New Close = Proposed New Close
       ▼
Commit to Database & Broadcast via WebSockets to all connected buyers and suppliers!
```

---

## 📄 Documentation Build Instructions

The deliverables in `docs/` (`HLD.pdf` and `Database_Schema.pdf`) are generated directly from the codebase using Python ReportLab and Matplotlib:

```bash
# Generate architecture, workflow, and ER diagrams:
python docs/generate_diagrams.py

# Compile publication-quality 3-page HLD and Database Schema PDFs:
python docs/build_pdfs.py
```

---

## 📌 Submission Note
All files are prepared locally and organized cleanly into `backend/`, `frontend/`, and `docs/`. Virtual environments, node modules, cache files, and private databases are excluded via `.gitignore`. You can review the files and push directly to your GitHub repository.
