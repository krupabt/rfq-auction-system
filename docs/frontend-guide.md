# Frontend Guide & Setup - British Auction RFQ System

## 1. Directory Structure

The frontend is a single-page application built with **React 19**, **Vite**, **TypeScript**, and **Tailwind CSS**, adhering to enterprise procurement design standards:

```
frontend/
├── src/
│   ├── assets/               # Static assets & icons
│   ├── components/           # Reusable UI components
│   │   ├── CountdownTimer.tsx      # Real-time countdown clock with trigger window alerts
│   │   ├── Header.tsx              # Top navigation bar with page title, breadcrumbs, user profile
│   │   ├── Sidebar.tsx             # Left navigation menu (Dashboard, RFQs, Auctions, Suppliers, etc.)
│   │   ├── StatusBadge.tsx         # Muted status indicators (SCHEDULED, ACTIVE, CLOSED, FORCE_CLOSED)
│   │   └── TriggerRuleBadge.tsx    # British Auction condition pills (Option A, B, C)
│   ├── context/
│   │   └── AuthContext.tsx         # JWT token storage, login/logout, authenticated user state
│   ├── layouts/
│   │   └── MainLayout.tsx          # Master application layout wrapping Header, Sidebar, and View Container
│   ├── pages/
│   │   ├── ActivityLogsPage.tsx    # Centralized audit trail and platform activity timeline
│   │   ├── AuctionDetailPage.tsx   # Core Auction Room: live clock, rules, rankings, quote form, history
│   │   ├── AuctionListingPage.tsx  # Dynamic auctions list with filters and countdown timers
│   │   ├── CreateRFQPage.tsx       # Multi-step RFQ creation form with British Auction rule configuration
│   │   ├── DashboardPage.tsx       # Overview statistics (Total RFQs, Active, Closed, Bids) & recent activity
│   │   ├── LoginPage.tsx           # Sign-in page with quick 1-click demo test account buttons
│   │   ├── RegisterPage.tsx        # Self-service registration for buyers and suppliers
│   │   ├── ReportsPage.tsx         # Procurement savings reports and auction performance analysis
│   │   ├── RFQManagementPage.tsx   # RFQ catalog and draft management
│   │   └── SuppliersPage.tsx       # Pre-qualified supplier directory
│   ├── services/
│   │   └── api.ts                  # Axios HTTP client with JWT Authorization interceptor
│   ├── App.tsx                     # Main router with protected routes and role checks
│   ├── index.css                   # Global Tailwind CSS definitions and Inter font imports
│   └── main.tsx                    # React application entry point (DOM root mount)
├── index.html                      # HTML5 entry page
├── package.json                    # Project dependencies and build scripts
├── tsconfig.json                   # TypeScript configuration
└── vite.config.ts                  # Vite build tool and API proxy configuration
```

---

## 2. Dependencies (`package.json`)

The application is powered by standard npm packages listed in `frontend/package.json`:

```json
{
  "dependencies": {
    "axios": "^1.21.0",
    "clsx": "^2.1.1",
    "lucide-react": "^1.67.0",
    "react": "^19.3.1",
    "react-dom": "^19.3.1",
    "react-router-dom": "^7.18.5",
    "tailwind-merge": "^3.7.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.3.4",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.2.1",
    "tailwindcss": "^4.3.4",
    "typescript": "~7.0.2",
    "vite": "^8.3.5"
  }
}
```

---

## 3. Step-by-Step Setup Instructions

### Step 1: Navigate to Frontend Directory
Open your terminal and navigate to the `frontend` folder:
```bash
cd frontend
```

### Step 2: Install Dependencies
Ensure **Node.js (v18+)** and **npm** are installed, then run:
```bash
npm install
```

### Step 3: Start the Vite Development Server
Start the frontend dev server:
```bash
npm run dev
```
The application will be available at:
- **Local Application URL**: `http://localhost:5173`

The development server is configured with a Vite proxy to forward all `/api` and `/ws` requests seamlessly to the FastAPI backend running on port `8000`.

### Step 4: Verify Production Build
To test the production build and verify that TypeScript compiles with 0 errors:
```bash
npm run build
```
Expected output:
```text
✓ built in 1.17s
dist/index.html                   0.77 kB │ gzip:   0.44 kB
dist/assets/index-6Fy6jwSY.css   20.43 kB │ gzip:   4.87 kB
dist/assets/index-BkhvEoSS.js   412.27 kB │ gzip: 120.05 kB
```

---

## 4. Design System & User Interface Rules

The UI strictly adheres to a minimalist enterprise design system:
- **Color Palette**:
  - Main Background: Pure White (`#FFFFFF`)
  - Sidebar & Cards: White (`#FFFFFF`) with subtle border lines
  - Primary Text: Solid Charcoal/Black (`#111111`)
  - Secondary Text: Slate Grey (`#777777`)
  - Borders: Light Grey (`#E5E5E5`)
  - Primary Buttons: Black background (`#111111`) with white text
  - Secondary Buttons: White background with black/grey borders
- **Typography**: Single typeface throughout — **Inter**
  - Page Headings: Inter, 24px, 600 weight
  - Section Headings: Inter, 16px, 600 weight
  - Normal Text: Inter, 14px, 400 weight
  - Table Headings: Inter, 12px, 600 weight (uppercase)
  - Buttons & Badges: Inter, 14px, 500 weight
- **Status Indicators**:
  - `ACTIVE`: Muted green badge (`#EBF7EE`, `#1E7E34`)
  - `SCHEDULED`: Muted blue badge (`#E8F4FD`, `#0B6BCB`)
  - `CLOSED`: Neutral grey badge (`#F2F2F2`, `#555555`)
  - `FORCE_CLOSED`: Muted amber badge (`#FFF8E1`, `#B36200`)

---

## 5. Live Auction Room & WebSocket Architecture

The core auction interaction is implemented in [`AuctionDetailPage.tsx`](file:///d:/gocomet-rfq-auction/frontend/src/pages/AuctionDetailPage.tsx):

1. **Auto Re-connection**: Establishes a WebSocket connection to `ws://localhost:8000/ws/auctions/{id}` on mount.
2. **Instant Sync**: When any participant places a bid or an extension triggers:
   - The countdown clock adjusts in real-time.
   - The **Supplier Rankings** leaderboard updates immediately without page reload.
   - The **Quote History** table appends the new bid chronologically.
   - The **Auction Activity** timeline logs the event.
3. **Multi-Supplier Presets**: The quote form allows each authenticated supplier to place competitive quotes with their operating carrier fleet, with built-in instant price calculations to test anti-sniping rules.
4. **Evaluator Fast-Forward**: Provides instant fast-forward buttons (`Trigger Window`, `30s Crunch`) allowing evaluators to skip waiting hours and observe automatic extensions in seconds.
