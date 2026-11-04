import os
import sys

# Add root directory and backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_dir = os.path.join(parent_dir, "backend")

for p in (parent_dir, backend_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

# On Vercel serverless, the filesystem is read-only except /tmp
if os.getenv("VERCEL"):
    os.environ["DATABASE_URL"] = "sqlite:////tmp/auction.db"

from backend.app.main import app
from backend.app.database import engine, Base, SessionLocal
from backend.app.seed import seed_database, ensure_demo_accounts

# Initialize database schema and demo accounts on cold start
try:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db, force_reset=False)
    ensure_demo_accounts(db)
    db.close()
except Exception as e:
    print(f"Serverless DB init error: {e}")
