from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, SessionLocal
from .seed import seed_database, ensure_demo_accounts
from .routes.auth import router as auth_router
from .routes.rfq import router as rfq_router
from .routes.auction import router as auction_router
from .routes.bid import router as bid_router
from .routes.dashboard import router as dashboard_router
from .routes.reports import router as reports_router
from .routes.websocket import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB schema
    Base.metadata.create_all(bind=engine)
    # Seed default users & auctions if empty
    db = SessionLocal()
    try:
        seed_database(db, force_reset=False)
        ensure_demo_accounts(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="British Auction – RFQ Management System",
    description="Enterprise reverse auction and freight RFQ platform with configurable dynamic extensions and forced close rules.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend (Vite port 5173 / localhost)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(rfq_router)
app.include_router(auction_router)
app.include_router(bid_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(websocket_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "British Auction RFQ Engine",
        "version": "2.0.0"
    }


@app.post("/api/seed")
def trigger_reseed(force: bool = Query(False, description="Wipe and cleanly reset all demo auctions & users")):
    db = SessionLocal()
    try:
        seed_database(db, force_reset=force)
        return {"status": "ok", "message": "Database successfully initialized with fresh demo data"}
    finally:
        db.close()
