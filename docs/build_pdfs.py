"""
Build professional PDF documentation for HLD and Database Schema using ReportLab Platypus.
Optimized for clean page budget and visual presentation.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        
        # Header (on all pages except page 1)
        if self._pageNumber > 1:
            self.drawString(54, letter[1] - 34, "British Auction in RFQ System - Submission Documentation")
            self.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 38, letter[0] - 54, letter[1] - 38)
        
        # Footer (on all pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 54, 28, page_text)
        self.drawString(54, 28, "British Auction in RFQ System")
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(54, 38, letter[0] - 54, 38)
        
        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    
    styles = {
        'DocTitle': ParagraphStyle(
            'DocTitle',
            parent=base['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=4
        ),
        'DocSubtitle': ParagraphStyle(
            'DocSubtitle',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#4B5563'),
            spaceAfter=8
        ),
        'H1': ParagraphStyle(
            'H1',
            parent=base['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        ),
        'H2': ParagraphStyle(
            'H2',
            parent=base['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#1F2937'),
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True
        ),
        'Body': ParagraphStyle(
            'Body',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=4
        ),
        'BodyBold': ParagraphStyle(
            'BodyBold',
            parent=base['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor('#111827'),
            spaceAfter=3
        ),
        'Bullet': ParagraphStyle(
            'Bullet',
            parent=base['Normal'],
            fontName='Helvetica',
            fontSize=7.8,
            leading=11,
            textColor=colors.HexColor('#374151'),
            leftIndent=10,
            spaceAfter=2
        ),
        'TableHead': ParagraphStyle(
            'TableHead',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#FFFFFF')
        ),
        'TableCell': ParagraphStyle(
            'TableCell',
            fontName='Helvetica',
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#1F2937')
        ),
        'TableCellBold': ParagraphStyle(
            'TableCellBold',
            fontName='Helvetica-Bold',
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#111827')
        ),
        'TableCellCode': ParagraphStyle(
            'TableCellCode',
            fontName='Courier-Bold',
            fontSize=7,
            leading=8.5,
            textColor=colors.HexColor('#1E40AF')
        )
    }
    return styles


def build_hld_pdf(output_path="docs/HLD.pdf"):
    styles = get_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=42
    )
    
    story = []
    
    # ---------------- PAGE 1 ----------------
    story.append(Paragraph("High-Level Design - British Auction in RFQ System", styles['DocTitle']))
    story.append(Paragraph("System Architecture, Anti-Sniping Engine & API Specifications", styles['DocSubtitle']))
    
    meta_table_data = [
        [
            Paragraph("<b>Project:</b> British Auction RFQ Management System", styles['TableCell']),
            Paragraph("<b>Architecture:</b> Decoupled 3-Tier Client-Server", styles['TableCell'])
        ],
        [
            Paragraph("<b>Frontend:</b> React 19, Vite, Tailwind CSS", styles['TableCell']),
            Paragraph("<b>Backend:</b> Python FastAPI 0.115, Uvicorn ASGI", styles['TableCell'])
        ],
        [
            Paragraph("<b>Real-Time:</b> Native HTML5 WebSockets", styles['TableCell']),
            Paragraph("<b>Database:</b> SQLite 3 with SQLAlchemy 2.0 ORM", styles['TableCell'])
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("1. Executive Overview & Problem Statement", styles['H1']))
    story.append(Paragraph(
        "In logistics procurement and commercial freight bidding, traditional fixed-deadline reverse auctions suffer from <b>bid sniping</b>: suppliers withhold their best rates until the final seconds to prevent counter-bids. This leads to artificial pressure, market distortion, and higher procurement costs for buyers.",
        styles['Body']
    ))
    story.append(Paragraph(
        "The <b>British Auction in RFQ System</b> overcomes bid sniping through dynamic anti-sniping rules: whenever competitive bidding activity occurs within the final <b>X minutes</b> (trigger window), the auction closing deadline is dynamically extended by <b>Y minutes</b>. Simultaneously, an immutable <b>Forced Bid Close Time</b> hard ceiling guarantees definitive operational closure.",
        styles['Body']
    ))
    
    story.append(Paragraph("2. System Architecture", styles['H1']))
    if os.path.exists("docs/architecture_diagram.png"):
        story.append(Image("docs/architecture_diagram.png", width=7.2*inch, height=3.3*inch))
        story.append(Spacer(1, 4))
    
    arch_cols = [
        [
            Paragraph("<b>Frontend Client Layer</b>", styles['TableCellBold']),
            Paragraph("<b>Backend API Layer</b>", styles['TableCellBold']),
            Paragraph("<b>Persistence Layer</b>", styles['TableCellBold'])
        ],
        [
            Paragraph("React 19 single-page application with Tailwind CSS. Role-based views for Admin, Buyer, and Supplier. Handles Axios REST API calls and persistent WebSocket streams.", styles['TableCell']),
            Paragraph("FastAPI asynchronous service powered by Uvicorn. Implements JWT authentication, RBAC authorization, British Auction domain logic, and real-time WebSocket connection manager.", styles['TableCell']),
            Paragraph("SQLite relational database managed via SQLAlchemy 2.0 ORM. Features 7 normalized tables, cascading constraints, unique indexes, and ACID transactional integrity.", styles['TableCell'])
        ]
    ]
    arch_table = Table(arch_cols, colWidths=[177, 178, 177])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EFF6FF')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(arch_table)
    
    story.append(PageBreak())
    
    # ---------------- PAGE 2 ----------------
    story.append(Paragraph("3. End-to-End British Auction Workflow & Lifecycle", styles['H1']))
    story.append(Paragraph(
        "The operational lifecycle coordinates buyer RFQ publication, supplier quote submissions, anti-sniping trigger evaluation, and sub-second WebSocket broadcasting:",
        styles['Body']
    ))
    
    if os.path.exists("docs/workflow_diagram.png"):
        story.append(Image("docs/workflow_diagram.png", width=7.2*inch, height=3.0*inch))
        story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>Step-by-Step Execution Sequence:</b>", styles['BodyBold']))
    story.append(Paragraph("<b>1. RFQ Publication:</b> Buyer creates RFQ (origin, destination, cargo, schedule) and configures British Auction parameters: trigger window <i>X</i>, extension duration <i>Y</i>, extension trigger condition (Option A, B, or C), and forced close ceiling.", styles['Bullet']))
    story.append(Paragraph("<b>2. Quote Submission:</b> Authorized suppliers submit detailed quotes (freight + origin + destination charges). The Auction Engine validates that quotes are strictly competitive (lower than the supplier's own previous best quote).", styles['Bullet']))
    story.append(Paragraph("<b>3. Anti-Sniping Evaluation:</b> When a quote arrives within the final <i>X</i> minutes, the engine checks if the trigger condition is satisfied.", styles['Bullet']))
    story.append(Paragraph("<b>4. Dynamic Time Extension:</b> If triggered, new closing time is calculated: <i>New Close = min(Current Close + Y, Forced Close)</i>. If Current Close + Y reaches or exceeds the forced ceiling, closing time clamps strictly to the ceiling.", styles['Bullet']))
    story.append(Paragraph("<b>5. Real-Time Synchronization:</b> The WebSocket manager instantly pushes updated leaderboards, countdown clocks, and extension banners to all connected clients without polling.", styles['Bullet']))
    story.append(Paragraph("<b>6. Auction Closure:</b> Once the countdown reaches zero or the forced close ceiling is hit, status transitions to CLOSED. No further bids are accepted.", styles['Bullet']))
    
    story.append(Spacer(1, 4))
    story.append(Paragraph("4. Core British Auction Rules & Anti-Sniping Options", styles['H1']))
    
    rule_table_data = [
        [
            Paragraph("Rule Name", styles['TableHead']),
            Paragraph("Implementation Specification", styles['TableHead']),
            Paragraph("Engine Behavior & Constraint", styles['TableHead'])
        ],
        [
            Paragraph("<b>Single Best Supplier Rule</b>", styles['TableCell']),
            Paragraph("Leaderboard aggregates exactly one entry per supplier.", styles['TableCell']),
            Paragraph("Each supplier's lowest total quote is ranked (L1, L2, L3, ...). Earlier submission timestamp wins ties.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Option A: ANY_BID</b>", styles['TableCell']),
            Paragraph("Any valid quote placed within last <i>X</i> minutes.", styles['TableCell']),
            Paragraph("Extends closing time by <i>Y</i> minutes, regardless of rank change. Maximizes competitive participation.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Option B: ANY_RANK_CHANGE</b>", styles['TableCell']),
            Paragraph("Any quote that shifts any position on leaderboard.", styles['TableCell']),
            Paragraph("Extends if quote moves supplier up (e.g., L3 to L2 or L2 to L1). Improvements that don't change rank do not extend.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Option C: L1_RANK_CHANGE</b>", styles['TableCell']),
            Paragraph("Only a quote establishing a new overall lowest price (L1).", styles['TableCell']),
            Paragraph("Extends only when market-leading rate is beaten. Default industry standard for procurement auctions.", styles['TableCell'])
        ],
        [
            Paragraph("<b>Forced Close Limit</b>", styles['TableCell']),
            Paragraph("<i>New_Close = min(Close + Y, Forced_Close)</i>", styles['TableCell']),
            Paragraph("Absolute hard ceiling. Bids attempted past forced close time are strictly rejected with HTTP 400.", styles['TableCell'])
        ]
    ]
    rule_table = Table(rule_table_data, colWidths=[115, 175, 242])
    rule_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')])
    ]))
    story.append(rule_table)
    
    story.append(PageBreak())
    
    # ---------------- PAGE 3 ----------------
    story.append(Paragraph("5. API & WebSocket Specifications", styles['H1']))
    story.append(Paragraph(
        "The backend exposes RESTful endpoints and bi-directional WebSocket streams documented via OpenAPI/Swagger:",
        styles['Body']
    ))
    
    api_table_data = [
        [
            Paragraph("Method / Route", styles['TableHead']),
            Paragraph("Access Role", styles['TableHead']),
            Paragraph("Purpose & Description", styles['TableHead'])
        ],
        [
            Paragraph("POST /api/auth/login", styles['TableCellCode']),
            Paragraph("Public", styles['TableCell']),
            Paragraph("Authenticates user with email/password; returns JWT bearer token.", styles['TableCell'])
        ],
        [
            Paragraph("GET /api/auth/me", styles['TableCellCode']),
            Paragraph("Authenticated", styles['TableCell']),
            Paragraph("Resolves active session profile, role permissions, and supplier linkage.", styles['TableCell'])
        ],
        [
            Paragraph("GET /api/rfqs", styles['TableCellCode']),
            Paragraph("Admin, Buyer", styles['TableCell']),
            Paragraph("Retrieves list of RFQs with status filtering (All, Scheduled, Active, Closed).", styles['TableCell'])
        ],
        [
            Paragraph("POST /api/rfqs", styles['TableCellCode']),
            Paragraph("Buyer", styles['TableCell']),
            Paragraph("Creates a new RFQ with British Auction rules (X, Y, trigger type, forced close).", styles['TableCell'])
        ],
        [
            Paragraph("GET /api/rfqs/{id}", styles['TableCellCode']),
            Paragraph("Authenticated", styles['TableCell']),
            Paragraph("Fetches RFQ details, cargo specifications, and British Auction configuration.", styles['TableCell'])
        ],
        [
            Paragraph("GET /api/auctions/{id}", styles['TableCellCode']),
            Paragraph("Authenticated", styles['TableCell']),
            Paragraph("Fetches live auction countdown, extension logs, and ranked supplier leaderboard.", styles['TableCell'])
        ],
        [
            Paragraph("POST /api/auctions/{id}/bids", styles['TableCellCode']),
            Paragraph("Supplier", styles['TableCell']),
            Paragraph("Submits competitive quote; triggers ranking recalculation & anti-sniping extension.", styles['TableCell'])
        ],
        [
            Paragraph("GET /api/auctions/{id}/bids", styles['TableCellCode']),
            Paragraph("Authenticated", styles['TableCell']),
            Paragraph("Returns chronological bidding history and itemized quote charge breakdowns.", styles['TableCell'])
        ],
        [
            Paragraph("GET /api/activity", styles['TableCellCode']),
            Paragraph("Authenticated", styles['TableCell']),
            Paragraph("Returns immutable audit trail of system events, bids, and auction extensions.", styles['TableCell'])
        ],
        [
            Paragraph("WS /ws/auctions/{id}", styles['TableCellCode']),
            Paragraph("Authenticated", styles['TableCell']),
            Paragraph("Persistent WebSocket stream for sub-second quote and extension broadcast.", styles['TableCell'])
        ]
    ]
    api_table = Table(api_table_data, colWidths=[150, 85, 297])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')])
    ]))
    story.append(api_table)
    
    story.append(Spacer(1, 6))
    story.append(Paragraph("6. Security, Reliability & Quality Assurance", styles['H1']))
    story.append(Paragraph(
        "<b>Security & Authentication:</b> Passwords hashed using bcrypt. Stateless authentication via cryptographically signed JWT tokens with expiration. Role-Based Access Control (RBAC) enforced at middleware and router levels.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Concurrency & Race Condition Handling:</b> Database transactions utilize scoped sessions with write locking to guarantee atomic quote evaluation, preventing simultaneous bids from corrupting leaderboard ranks or close times.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Automated Test Suite:</b> Comprehensive test coverage (17/17 tests passing) validating all extension trigger types (A, B, C), tie-breaking, forced-close clamping, role authorization, and quote validation.",
        styles['Body']
    ))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated {output_path} (Clean 3-Page Layout)")


def build_db_schema_pdf(output_path="docs/Database_Schema.pdf"):
    styles = get_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=42
    )
    
    story = []
    
    # ---------------- PAGE 1 ----------------
    story.append(Paragraph("Database Schema Design - British Auction in RFQ System", styles['DocTitle']))
    story.append(Paragraph("Entity-Relationship (ER) Diagram & Relational Data Dictionary", styles['DocSubtitle']))
    
    meta_table_data = [
        [
            Paragraph("<b>Database Engine:</b> SQLite 3 Relational Database", styles['TableCell']),
            Paragraph("<b>ORM:</b> SQLAlchemy 2.0 (Declarative Base)", styles['TableCell'])
        ],
        [
            Paragraph("<b>Normalization:</b> Third Normal Form (3NF)", styles['TableCell']),
            Paragraph("<b>Integrity:</b> Foreign Key Constraints & Cascade Delete", styles['TableCell'])
        ],
        [
            Paragraph("<b>Total Tables:</b> 7 Core Normalized Entities", styles['TableCell']),
            Paragraph("<b>File Location:</b> backend/auction.db", styles['TableCell'])
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[260, 272])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))
    
    story.append(Paragraph("1. Database Architecture & Design Principles", styles['H1']))
    story.append(Paragraph(
        "The British Auction RFQ database schema is structured into <b>7 normalized relational tables</b> designed to decouple user authentication, supplier commercial profiles, procurement RFQ specifications, British auction configuration parameters, quote transactions, dynamic time extensions, and audit trails.",
        styles['Body']
    ))
    story.append(Paragraph("<b>Core Schema Design Pillars:</b>", styles['BodyBold']))
    story.append(Paragraph("<b>- Referential Integrity:</b> Enforced using foreign key constraints with cascading deletion rules (e.g. deleting an RFQ removes its configuration, quote records, and extension logs cleanly).", styles['Bullet']))
    story.append(Paragraph("<b>- High-Throughput Indexing:</b> Unique and B-Tree indexes placed on lookup keys: <code>email</code>, <code>reference_id</code>, <code>rfq_id</code>, <code>supplier_id</code>, <code>submitted_at</code>, and <code>total_quote</code>.", styles['Bullet']))
    story.append(Paragraph("<b>- Complete Auditability:</b> Dedicated <code>activity_logs</code> table records every administrative, bidding, and extension action as an immutable chronological ledger.", styles['Bullet']))
    
    story.append(Paragraph("2. Entity-Relationship (ER) Diagram", styles['H1']))
    if os.path.exists("docs/er_diagram.png"):
        story.append(Image("docs/er_diagram.png", width=7.2*inch, height=3.6*inch))
        story.append(Spacer(1, 4))
    
    story.append(PageBreak())
    
    # ---------------- PAGE 2: Tables 1, 2, 3 ----------------
    story.append(Paragraph("3. Detailed Data Dictionary & Table Definitions", styles['H1']))
    
    def make_table_def(title, desc, columns):
        elements = [
            Paragraph(f"<b>Table: {title}</b> — {desc}", styles['H2']),
            Spacer(1, 1)
        ]
        table_rows = [
            [
                Paragraph("Column Name", styles['TableHead']),
                Paragraph("Data Type", styles['TableHead']),
                Paragraph("Constraints & Keys", styles['TableHead']),
                Paragraph("Description & Purpose", styles['TableHead'])
            ]
        ]
        for col_name, col_type, constraints, col_desc in columns:
            table_rows.append([
                Paragraph(col_name, styles['TableCellCode']),
                Paragraph(col_type, styles['TableCell']),
                Paragraph(constraints, styles['TableCellBold'] if 'PK' in constraints or 'FK' in constraints else styles['TableCell']),
                Paragraph(col_desc, styles['TableCell'])
            ])
        t = Table(table_rows, colWidths=[105, 75, 122, 230])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')])
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))
        return elements

    # 1. users
    story.extend(make_table_def("users", "User credentials, access roles, and platform status", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique identifier for user account"),
        ("full_name", "VARCHAR(255)", "NOT NULL", "Full legal name of user"),
        ("email", "VARCHAR(255)", "NOT NULL, UNIQUE, INDEX", "Work email address used for login"),
        ("hashed_password", "VARCHAR(255)", "NOT NULL", "Salted bcrypt hash of user password"),
        ("role", "VARCHAR(20)", "NOT NULL", "System role: ADMIN, BUYER, or SUPPLIER"),
        ("is_active", "BOOLEAN", "NOT NULL, DEFAULT TRUE", "Active account toggle"),
        ("created_at", "DATETIME", "NOT NULL, DEFAULT UTC", "Account creation timestamp")
    ]))

    # 2. suppliers
    story.extend(make_table_def("suppliers", "Company details for registered logistics suppliers and carrier operators", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique supplier entity identifier"),
        ("user_id", "INTEGER", "NOT NULL, UNIQUE, FK -> users.id", "Reference to parent user account"),
        ("company_name", "VARCHAR(255)", "NOT NULL, UNIQUE, INDEX", "Registered business name (e.g. Maersk)"),
        ("contact_person", "VARCHAR(255)", "NOT NULL", "Primary representative contact name"),
        ("phone", "VARCHAR(50)", "NULLABLE", "Contact telephone number"),
        ("address", "VARCHAR(500)", "NULLABLE", "Registered corporate business address"),
        ("created_at", "DATETIME", "NOT NULL, DEFAULT UTC", "Supplier registration timestamp")
    ]))

    # 3. rfqs
    story.extend(make_table_def("rfqs", "Request for Quotations (RFQs) published by buyers", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique RFQ record identifier"),
        ("reference_id", "VARCHAR(50)", "NOT NULL, UNIQUE, INDEX", "Human-readable identifier (e.g. GC-RFQ-2026-001)"),
        ("name", "VARCHAR(255)", "NOT NULL, INDEX", "Procurement title or freight route name"),
        ("description", "TEXT", "NULLABLE", "Detailed shipping cargo requirements"),
        ("buyer_id", "INTEGER", "NOT NULL, FK -> users.id", "Reference to buyer user creating the RFQ"),
        ("origin / destination", "VARCHAR(255)", "NOT NULL", "Origin and Destination seaport/airport locations"),
        ("cargo_details", "VARCHAR(255)", "NULLABLE", "Cargo volume, weight, container type"),
        ("pickup_service_date", "DATETIME", "NOT NULL", "Expected cargo pickup date"),
        ("bid_start_time", "DATETIME", "NOT NULL", "Scheduled start time when bidding opens"),
        ("original_bid_close_time", "DATETIME", "NOT NULL", "Original scheduled closing time"),
        ("current_bid_close_time", "DATETIME", "NOT NULL, INDEX", "Effective closing time (dynamically extended)"),
        ("forced_bid_close_time", "DATETIME", "NOT NULL", "Absolute maximum forced close ceiling"),
        ("status", "VARCHAR(20)", "NOT NULL", "Status: SCHEDULED, ACTIVE, CLOSED, FORCE_CLOSED"),
        ("is_british_auction", "BOOLEAN", "NOT NULL, DEFAULT TRUE", "Enables British Auction anti-sniping rules"),
        ("target_price", "FLOAT", "NULLABLE", "Internal baseline benchmark price"),
        ("created_at / updated_at", "DATETIME", "NOT NULL, DEFAULT UTC", "Audit timestamps for record creation/update")
    ]))

    story.append(PageBreak())

    # ---------------- PAGE 3: Tables 4, 5, 6, 7 ----------------
    story.append(Paragraph("3. Detailed Data Dictionary (Continued)", styles['H1']))

    # 4. auction_configurations
    story.extend(make_table_def("auction_configurations", "British Auction parameters for each RFQ", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique configuration identifier"),
        ("rfq_id", "INTEGER", "NOT NULL, UNIQUE, FK -> rfqs.id", "Parent RFQ reference (1-to-1 relationship)"),
        ("trigger_window_minutes", "FLOAT", "NOT NULL, DEFAULT 10.0", "X minutes: Anti-sniping monitoring window"),
        ("extension_duration_minutes", "FLOAT", "NOT NULL, DEFAULT 5.0", "Y minutes: Time added per qualifying trigger"),
        ("extension_trigger_type", "VARCHAR(30)", "NOT NULL", "Trigger condition: ANY_BID, ANY_RANK_CHANGE, or L1_RANK_CHANGE"),
        ("created_at", "DATETIME", "NOT NULL, DEFAULT UTC", "Configuration timestamp")
    ]))

    # 5. auction_extensions
    story.extend(make_table_def("auction_extensions", "Audit trail of each dynamic time extension event", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique extension record identifier"),
        ("rfq_id", "INTEGER", "NOT NULL, INDEX, FK -> rfqs.id", "Target RFQ reference"),
        ("previous_close_time", "DATETIME", "NOT NULL", "Closing timestamp prior to this extension"),
        ("new_close_time", "DATETIME", "NOT NULL", "Extended closing timestamp"),
        ("extension_duration", "FLOAT", "NOT NULL", "Minutes added by this extension"),
        ("trigger_reason", "TEXT", "NOT NULL", "Detailed explanation of trigger and supplier"),
        ("triggering_bid_id", "INTEGER", "NULLABLE, FK -> bids.id", "Specific quote that triggered the extension"),
        ("created_at", "DATETIME", "NOT NULL, DEFAULT UTC", "Timestamp when extension was calculated")
    ]))

    # 6. bids
    story.extend(make_table_def("bids", "Quotes submitted by suppliers with price breakdown and carrier data", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique quote identifier"),
        ("rfq_id", "INTEGER", "NOT NULL, INDEX, FK -> rfqs.id", "Target RFQ reference"),
        ("supplier_id", "INTEGER", "NOT NULL, INDEX, FK -> suppliers.id", "Submitting supplier account reference"),
        ("carrier_name", "VARCHAR(255)", "NOT NULL", "Operating ocean carrier or airline fleet name"),
        ("freight_charges", "FLOAT", "NOT NULL", "Base ocean / air freight transportation price"),
        ("origin / dest_charges", "FLOAT", "NOT NULL, DEFAULT 0.0", "Origin THC and destination discharge port charges"),
        ("total_quote", "FLOAT", "NOT NULL, INDEX", "Calculated sum: freight + origin + destination"),
        ("transit_time", "INTEGER", "NOT NULL", "Estimated cargo transit duration in days"),
        ("validity_of_quote", "DATETIME", "NOT NULL", "Quote rate validity expiration timestamp"),
        ("submitted_at", "DATETIME", "NOT NULL, INDEX, DEFAULT UTC", "Precise submission timestamp"),
        ("is_valid", "BOOLEAN", "NOT NULL, DEFAULT TRUE", "Active/valid status flag"),
        ("rank_at_submission", "INTEGER", "NULLABLE", "Rank achieved at moment of submission")
    ]))

    # 7. activity_logs
    story.extend(make_table_def("activity_logs", "Immutable audit trail of system, RFQ, and auction events", [
        ("id", "INTEGER", "PRIMARY KEY, AUTO", "Unique audit log identifier"),
        ("rfq_id", "INTEGER", "NULLABLE, INDEX, FK -> rfqs.id", "Associated RFQ (if applicable)"),
        ("user_id", "INTEGER", "NULLABLE, INDEX, FK -> users.id", "User who initiated the action"),
        ("event_type", "VARCHAR(50)", "NOT NULL", "Event category (RFQ_CREATED, BID_SUBMITTED, etc.)"),
        ("description", "TEXT", "NOT NULL", "Human-readable event narrative"),
        ("created_at", "DATETIME", "NOT NULL, INDEX, DEFAULT UTC", "Event creation timestamp")
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated {output_path} (Clean 3-Page Layout)")

if __name__ == '__main__':
    build_hld_pdf()
    build_db_schema_pdf()
