"""
Script to generate diagrams for HLD and Database Schema documentation.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_architecture_diagram(output_path="docs/architecture_diagram.png"):
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Background
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Draw Layers
    # Layer 1: Frontend Client Layer
    box_client = patches.FancyBboxPatch((4, 66), 92, 28, boxstyle="round,pad=1.5,rounding_size=2",
                                        facecolor="#EFF6FF", edgecolor="#3B82F6", linewidth=1.5)
    ax.add_patch(box_client)
    ax.text(6, 91, "Frontend Client Layer (React 19 + Vite + Tailwind CSS)", fontsize=11, fontweight='bold', color="#1E40AF")

    # Frontend Components
    comps_frontend = [
        ("React UI Pages", "Admin, Buyer & Supplier Dashboards,\nRFQ Management, Auction Monitor", 6, 69, 26, 18),
        ("State & Auth Context", "JWT Token Storage, Role-Based Access\nProtected Routes (Buyer/Supplier)", 37, 69, 27, 18),
        ("Communication Clients", "Axios (REST API Calls)\nWebSocket Client (Live Updates)", 68, 69, 26, 18)
    ]
    for title, desc, x, y, w, h in comps_frontend:
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1,rounding_size=1.5",
                                   facecolor="#FFFFFF", edgecolor="#93C5FD", linewidth=1.2)
        ax.add_patch(p)
        ax.text(x + w/2, y + h - 4, title, fontsize=9, fontweight='bold', ha='center', color="#1E3A8A")
        ax.text(x + w/2, y + 5, desc, fontsize=7.5, ha='center', va='center', color="#4B5563")

    # Arrows between Client & Backend
    ax.annotate("", xy=(30, 58), xytext=(30, 66),
                arrowprops=dict(arrowstyle="<->", color="#2563EB", lw=1.8))
    ax.text(32, 61.5, "HTTP REST (JSON / JWT)", fontsize=8, fontweight='bold', color="#2563EB")

    ax.annotate("", xy=(78, 58), xytext=(78, 66),
                arrowprops=dict(arrowstyle="<->", color="#059669", lw=1.8))
    ax.text(80, 61.5, "WebSocket (Live Events)", fontsize=8, fontweight='bold', color="#059669")

    # Layer 2: Backend API Layer
    box_backend = patches.FancyBboxPatch((4, 28), 92, 30, boxstyle="round,pad=1.5,rounding_size=2",
                                         facecolor="#F0FDF4", edgecolor="#10B981", linewidth=1.5)
    ax.add_patch(box_backend)
    ax.text(6, 55, "Backend Service Layer (FastAPI + Python 3.12 + Uvicorn ASGI)", fontsize=11, fontweight='bold', color="#065F46")

    comps_backend = [
        ("REST API Routers", "/api/auth  |  /api/rfqs\n/api/auctions  |  /api/bids\n/api/activity", 6, 31, 26, 20),
        ("British Auction Engine", "L1/L2/L3 Ranking, Anti-Sniping\nTriggers (A/B/C), Forced Close Cap", 37, 31, 27, 20),
        ("WebSocket Manager", "Client Connection Registry\nSub-second Event Broadcasting", 68, 31, 26, 20)
    ]
    for title, desc, x, y, w, h in comps_backend:
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1,rounding_size=1.5",
                                   facecolor="#FFFFFF", edgecolor="#A7F3D0", linewidth=1.2)
        ax.add_patch(p)
        ax.text(x + w/2, y + h - 4.5, title, fontsize=9, fontweight='bold', ha='center', color="#064E3B")
        ax.text(x + w/2, y + 6, desc, fontsize=7.5, ha='center', va='center', color="#4B5563")

    # Arrows between Backend & DB
    ax.annotate("", xy=(50, 18), xytext=(50, 28),
                arrowprops=dict(arrowstyle="<->", color="#4B5563", lw=1.8))
    ax.text(52, 22.5, "SQLAlchemy 2.0 ORM (Queries & Transactions)", fontsize=8, fontweight='bold', color="#374151")

    # Layer 3: Persistence Layer
    box_db = patches.FancyBboxPatch((4, 3), 92, 15, boxstyle="round,pad=1.5,rounding_size=2",
                                    facecolor="#F9FAFB", edgecolor="#6B7280", linewidth=1.5)
    ax.add_patch(box_db)
    ax.text(6, 15.5, "Persistence Layer (Relational Storage)", fontsize=11, fontweight='bold', color="#1F2937")

    p_db = patches.FancyBboxPatch((15, 4.5), 70, 9, boxstyle="round,pad=1,rounding_size=1.5",
                                  facecolor="#FFFFFF", edgecolor="#D1D5DB", linewidth=1.2)
    ax.add_patch(p_db)
    ax.text(50, 9, "SQLite Database (auction.db)  |  7 Normalized Tables with Foreign Keys & Indexes",
            fontsize=8.5, fontweight='bold', ha='center', va='center', color="#111827")

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated {output_path}")

def generate_workflow_diagram(output_path="docs/workflow_diagram.png"):
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    steps = [
        ("1. Create RFQ", "Buyer publishes RFQ\nConfigures X, Y and\nExtension Trigger (A/B/C)", 3, 50, 17, 38, "#EFF6FF", "#3B82F6"),
        ("2. Submit Quotes", "Suppliers submit quotes\nTotal = Freight + Origin\n+ Destination charges", 23, 50, 17, 38, "#F0FDF4", "#10B981"),
        ("3. Evaluate Trigger", "Quote in final X mins?\nRule satisfied? (Option A, B, or C)\nChecks Hard Close Limit", 43, 50, 18, 38, "#FEF3C7", "#F59E0B"),
        ("4. Dynamic Extension", "Extend close time by Y min:\nNew = min(Current + Y,\nForced Bid Close Time)", 64, 50, 17, 38, "#EDE9FE", "#8B5CF6"),
        ("5. Real-Time Sync", "WebSocket pushes updates\nLeaderboard refreshed\nAudit log persisted", 83, 50, 15, 38, "#FEE2E2", "#EF4444"),
    ]

    for title, desc, x, y, w, h, bg, border in steps:
        p = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1,rounding_size=1.5",
                                   facecolor=bg, edgecolor=border, linewidth=1.5)
        ax.add_patch(p)
        ax.text(x + w/2, y + h - 7, title, fontsize=9, fontweight='bold', ha='center', color="#111827")
        ax.text(x + w/2, y + 15, desc, fontsize=7.5, ha='center', va='center', color="#374151")

    # Arrows between workflow steps
    for i in range(len(steps) - 1):
        x_start = steps[i][2] + steps[i][4]
        x_end = steps[i+1][2]
        y_mid = 69
        ax.annotate("", xy=(x_end - 0.5, y_mid), xytext=(x_start + 0.5, y_mid),
                    arrowprops=dict(arrowstyle="->", color="#374151", lw=2, mutation_scale=12))

    # Anti-sniping decision banner at bottom
    p_banner = patches.FancyBboxPatch((3, 6), 95, 34, boxstyle="round,pad=1,rounding_size=2",
                                      facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.2)
    ax.add_patch(p_banner)
    ax.text(50, 34, "British Auction Dynamic Anti-Sniping Engine Logic", fontsize=9.5, fontweight='bold', ha='center', color="#0F172A")

    rules_text = (
        "• Option A (ANY_BID): Any valid quote placed within last X minutes extends auction by Y minutes.\n"
        "• Option B (ANY_RANK_CHANGE): Any quote changing any supplier's leaderboard rank within last X minutes extends auction.\n"
        "• Option C (L1_RANK_CHANGE): Only a quote creating a new lowest price (L1 leader) within last X minutes extends auction.\n"
        "• Forced Close Protection: Auction NEVER extends past Forced Bid Close Time ceiling under any condition."
    )
    ax.text(6, 18, rules_text, fontsize=8, ha='left', va='center', color="#334155", linespacing=1.6)

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated {output_path}")

def generate_er_diagram(output_path="docs/er_diagram.png"):
    fig, ax = plt.subplots(figsize=(10.5, 6), dpi=300)
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 100)
    ax.axis('off')

    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    # Tables with coordinates and attributes
    # users (left top)
    # suppliers (left bottom)
    # rfqs (center top)
    # auction_configurations (top right)
    # auction_extensions (bottom right)
    # bids (center bottom)
    # activity_logs (far bottom right)

    tables = [
        ("users", 3, 56, 25, 40, [
            ("id", "INTEGER (PK)"),
            ("full_name", "VARCHAR(255)"),
            ("email", "VARCHAR(255) UK"),
            ("hashed_password", "VARCHAR(255)"),
            ("role", "VARCHAR(20)"),
            ("is_active", "BOOLEAN"),
            ("created_at", "DATETIME")
        ]),
        ("suppliers", 3, 6, 25, 42, [
            ("id", "INTEGER (PK)"),
            ("user_id", "INTEGER (FK,UK)"),
            ("company_name", "VARCHAR(255) UK"),
            ("contact_person", "VARCHAR(255)"),
            ("phone", "VARCHAR(50)"),
            ("address", "VARCHAR(500)"),
            ("created_at", "DATETIME")
        ]),
        ("rfqs", 38, 52, 29, 44, [
            ("id", "INTEGER (PK)"),
            ("reference_id", "VARCHAR(50) UK"),
            ("name", "VARCHAR(255)"),
            ("buyer_id", "INTEGER (FK)"),
            ("origin / destination", "VARCHAR(255)"),
            ("bid_start_time", "DATETIME"),
            ("current_bid_close", "DATETIME"),
            ("forced_bid_close", "DATETIME"),
            ("status", "VARCHAR(20)"),
            ("is_british_auction", "BOOLEAN")
        ]),
        ("auction_configurations", 75, 66, 27, 30, [
            ("id", "INTEGER (PK)"),
            ("rfq_id", "INTEGER (FK,UK)"),
            ("trigger_window_minutes", "FLOAT (X)"),
            ("extension_duration_minutes", "FLOAT (Y)"),
            ("extension_trigger_type", "VARCHAR(30)"),
            ("created_at", "DATETIME")
        ]),
        ("bids", 38, 4, 29, 42, [
            ("id", "INTEGER (PK)"),
            ("rfq_id", "INTEGER (FK)"),
            ("supplier_id", "INTEGER (FK)"),
            ("carrier_name", "VARCHAR(255)"),
            ("freight_charges", "FLOAT"),
            ("origin / dest_charges", "FLOAT"),
            ("total_quote", "FLOAT"),
            ("submitted_at", "DATETIME"),
            ("rank_at_submission", "INTEGER")
        ]),
        ("auction_extensions", 75, 34, 27, 28, [
            ("id", "INTEGER (PK)"),
            ("rfq_id", "INTEGER (FK)"),
            ("previous_close_time", "DATETIME"),
            ("new_close_time", "DATETIME"),
            ("trigger_reason", "TEXT"),
            ("triggering_bid_id", "INTEGER (FK)")
        ]),
        ("activity_logs", 75, 4, 27, 26, [
            ("id", "INTEGER (PK)"),
            ("rfq_id", "INTEGER (FK)"),
            ("user_id", "INTEGER (FK)"),
            ("event_type", "VARCHAR(50)"),
            ("description", "TEXT"),
            ("created_at", "DATETIME")
        ])
    ]

    for name, x, y, w, h, cols in tables:
        # Header box
        header = patches.FancyBboxPatch((x, y + h - 8), w, 8, boxstyle="round,pad=0.2,rounding_size=1",
                                        facecolor="#1E3A8A", edgecolor="#1E3A8A", linewidth=1)
        ax.add_patch(header)
        ax.text(x + w/2, y + h - 4, name.upper(), fontsize=8.5, fontweight='bold', ha='center', va='center', color="#FFFFFF")

        # Body box
        body = patches.FancyBboxPatch((x, y), w, h - 8, boxstyle="square,pad=0.2",
                                      facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=1)
        ax.add_patch(body)

        # Columns
        line_y = y + h - 12
        for col_name, col_type in cols:
            ax.text(x + 1.5, line_y, col_name, fontsize=6.8, fontweight='bold' if 'PK' in col_type or 'FK' in col_type else 'normal',
                    color="#0F172A" if 'PK' in col_type or 'FK' in col_type else "#334155")
            ax.text(x + w - 1.5, line_y, col_type, fontsize=6.2, ha='right', color="#64748B")
            line_y -= (h - 11) / len(cols)

    # Relationship connectors
    # users -> suppliers (1 to 1)
    ax.annotate("", xy=(15, 48), xytext=(15, 56),
                arrowprops=dict(arrowstyle="-", color="#2563EB", lw=1.3, linestyle="dashed"))
    ax.text(16.5, 51.5, "1:1", fontsize=7.5, fontweight='bold', color="#2563EB")

    # users -> rfqs (1 to N)
    ax.annotate("", xy=(38, 76), xytext=(28, 76),
                arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.3))
    ax.text(31, 78, "1 : N", fontsize=7.5, fontweight='bold', color="#2563EB")

    # rfqs -> auction_configurations (1 to 1)
    ax.annotate("", xy=(75, 80), xytext=(67, 80),
                arrowprops=dict(arrowstyle="-", color="#059669", lw=1.3))
    ax.text(69.5, 82, "1 : 1", fontsize=7.5, fontweight='bold', color="#059669")

    # rfqs -> bids (1 to N)
    ax.annotate("", xy=(52, 46), xytext=(52, 52),
                arrowprops=dict(arrowstyle="->", color="#D97706", lw=1.3))
    ax.text(53.5, 48.5, "1 : N", fontsize=7.5, fontweight='bold', color="#D97706")

    # suppliers -> bids (1 to N)
    ax.annotate("", xy=(38, 25), xytext=(28, 25),
                arrowprops=dict(arrowstyle="->", color="#D97706", lw=1.3))
    ax.text(31, 27, "1 : N", fontsize=7.5, fontweight='bold', color="#D97706")

    # rfqs -> auction_extensions (1 to N)
    ax.annotate("", xy=(75, 50), xytext=(67, 60),
                arrowprops=dict(arrowstyle="->", color="#7C3AED", lw=1.3))
    ax.text(69, 56, "1 : N", fontsize=7.5, fontweight='bold', color="#7C3AED")

    # bids -> auction_extensions (1 to 1)
    ax.annotate("", xy=(75, 42), xytext=(67, 30),
                arrowprops=dict(arrowstyle="-", color="#7C3AED", lw=1.3, linestyle="dotted"))

    # rfqs -> activity_logs (1 to N)
    ax.annotate("", xy=(75, 18), xytext=(67, 18),
                arrowprops=dict(arrowstyle="->", color="#4B5563", lw=1.3))
    ax.text(69, 20, "1 : N", fontsize=7.5, fontweight='bold', color="#4B5563")

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated {output_path}")

if __name__ == '__main__':
    generate_architecture_diagram()
    generate_workflow_diagram()
    generate_er_diagram()
