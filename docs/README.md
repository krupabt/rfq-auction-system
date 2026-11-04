# British Auction in RFQ System - Project Documentation & Deliverables

## 1. Project Overview

This repository contains the complete implementation of the **British Auction – RFQ Management System**. It is an enterprise-grade procurement and supplier bidding platform developed with **React + Vite**, **Python FastAPI**, **SQLAlchemy ORM**, **SQLite**, and **WebSockets**.

---

## 2. Deliverables Index

All submission documentation is organized within the `docs/` folder:

| Document | File Link | Description |
| :--- | :--- | :--- |
| **High-Level Design (HLD)** | [high-level-design.md](file:///d:/gocomet-rfq-auction/docs/high-level-design.md) | Architectural architecture diagrams, component breakdown, REST & WebSocket protocols, and end-to-end workflow from RFQ creation to forced closing. |
| **Database Schema Design** | [database-schema.md](file:///d:/gocomet-rfq-auction/docs/database-schema.md) | Verified documentation of all 7 SQLAlchemy models/tables, column data types, constraints, primary & foreign keys, relationships, and a full Mermaid ER diagram. |
| **Backend Code & Setup** | [backend-guide.md](file:///d:/gocomet-rfq-auction/docs/backend-guide.md) | Complete backend directory structure, FastAPI endpoints reference, British Auction Engine rules, `requirements.txt`, setup commands, and pytest test suite. |
| **Frontend Code & Setup** | [frontend-guide.md](file:///d:/gocomet-rfq-auction/docs/frontend-guide.md) | Frontend directory structure, React 19 + Vite architecture, component hierarchy, minimal black & white design system, `package.json`, and setup commands. |

---

## 3. Demo Test Accounts

The platform includes pre-seeded demo accounts with one-click autofill buttons on the login page:

| Role | Email Address | Password | Profile / Company Name |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@gocomet.com` | `admin123` | Global Procurement Admin |
| **Buyer** | `buyer@gocomet.com` | `buyer123` | Senior Logistics Buyer (GoComet) |
| **Supplier 1** | `supplier@gocomet.com` | `supplier123` | A.P. Moller - Maersk |
| **Supplier 2** | `msc@carrier.com` | `supplier123` | MSC Mediterranean Shipping Co. |
| **Supplier 3** | `hapag@carrier.com` | `supplier123` | Hapag-Lloyd AG |
| **Supplier 4** | `cmacgm@carrier.com` | `supplier123` | CMA CGM Group |

---

## 4. Quick Start Commands

### Start Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API URL: `http://127.0.0.1:8000`
- Interactive API Docs: `http://127.0.0.1:8000/docs`

### Start Frontend Server
```bash
cd frontend
npm run dev
```
- Application URL: `http://localhost:5173`

### Run Backend Automated Tests
```bash
cd backend
pytest -v
```

---

## 5. Deliverables Submission Checklist

| # | Required Deliverable | Status | Notes |
| :---: | :--- | :---: | :--- |
| 1 | **High-Level Design (HLD)** | ✅ Ready | Complete architecture diagram, REST & WebSocket communication, and workflow in `docs/high-level-design.md`. |
| 2 | **Database Schema Design** | ✅ Ready | All 7 verified tables, exact data types, constraints, relationships, and Mermaid ER diagram in `docs/database-schema.md`. |
| 3 | **Backend Code & Setup** | ✅ Ready | Full source code, `requirements.txt`, setup guide, and 11 passing automated tests in `docs/backend-guide.md`. |
| 4 | **Frontend Code & Setup** | ✅ Ready | Full source code, `package.json`, setup guide, and verified production build in `docs/frontend-guide.md`. |
| 5 | **British Auction Logic** | ✅ Ready | Anti-sniping trigger options (A, B, C) and forced-close ceiling fully operational and tested. |
| 6 | **Multi-Supplier Support** | ✅ Ready | Distinct supplier rankings (L1, L2, L3) and carrier identity verified with 4 active supplier profiles. |
| 7 | **Audit Trail & Logs** | ✅ Ready | Real-time event tracking across rankings, quotes, and audit logs. |
| 8 | **Design & Technology Stack** | ✅ Ready | Clean black & white theme (#FFFFFF / #111111 / #E5E5E5) with Inter typography; React + Vite + FastAPI + SQLite. |
