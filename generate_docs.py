"""Generate Airfinder complete project documentation PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
import datetime

# ── Brand colors ───────────────────────────────────────────────────────────────
GREEN       = colors.HexColor('#407E3C')
GREEN_LIGHT = colors.HexColor('#EBF5E8')
GREEN_MID   = colors.HexColor('#5a9e56')
DARK        = colors.HexColor('#1a1a1a')
GRAY        = colors.HexColor('#6B7280')
GRAY_LIGHT  = colors.HexColor('#F3F4F6')
GRAY_BORDER = colors.HexColor('#E5E7EB')
WHITE       = colors.white
AMBER       = colors.HexColor('#D97706')
BLUE        = colors.HexColor('#2563EB')
RED         = colors.HexColor('#DC2626')

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Page numbering ─────────────────────────────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for i, state in enumerate(self._saved_page_states):
            self.__dict__.update(state)
            self._draw_footer(i + 1, total)
            super().showPage()
        super().save()

    def _draw_footer(self, page_num, total):
        self.saveState()
        # Footer line
        self.setStrokeColor(GRAY_BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN, 1.4 * cm, PAGE_W - MARGIN, 1.4 * cm)
        # Left: brand
        self.setFillColor(GREEN)
        self.setFont('Helvetica-Bold', 8)
        self.drawString(MARGIN, 0.9 * cm, 'Airfinder')
        # Center: doc title
        self.setFillColor(GRAY)
        self.setFont('Helvetica', 8)
        self.drawCentredString(PAGE_W / 2, 0.9 * cm, 'Project Documentation — Confidential')
        # Right: page number
        self.setFillColor(GRAY)
        self.setFont('Helvetica', 8)
        self.drawRightString(PAGE_W - MARGIN, 0.9 * cm, f'Page {page_num} of {total}')
        self.restoreState()


# ── Styles ─────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

H1 = S('H1', fontSize=26, textColor=DARK, fontName='Helvetica-Bold',
        spaceAfter=10, spaceBefore=0, leading=32)
H2 = S('H2', fontSize=18, textColor=GREEN, fontName='Helvetica-Bold',
        spaceAfter=8, spaceBefore=20, leading=24, keepWithNext=1)
H3 = S('H3', fontSize=13, textColor=DARK, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=14, leading=18, keepWithNext=1)
H4 = S('H4', fontSize=11, textColor=GREEN, fontName='Helvetica-Bold',
        spaceAfter=4, spaceBefore=10, leading=16, keepWithNext=1)
BODY = S('BODY', fontSize=10, textColor=DARK, fontName='Helvetica',
         spaceAfter=6, spaceBefore=2, leading=16, alignment=TA_JUSTIFY)
BODY_SM = S('BODY_SM', fontSize=9, textColor=DARK, fontName='Helvetica',
            spaceAfter=4, spaceBefore=2, leading=14)
CAPTION = S('CAPTION', fontSize=8.5, textColor=GRAY, fontName='Helvetica-Oblique',
            spaceAfter=4, spaceBefore=2, leading=13)
CODE = S('CODE', fontSize=8.5, textColor=colors.HexColor('#1e3a5f'),
         fontName='Courier', spaceAfter=3, spaceBefore=3, leading=13,
         backColor=colors.HexColor('#F0F4F8'), leftIndent=8)
BULLET = S('BULLET', fontSize=10, textColor=DARK, fontName='Helvetica',
           spaceAfter=4, spaceBefore=2, leading=15, leftIndent=14,
           bulletIndent=4)
NOTE = S('NOTE', fontSize=9.5, textColor=colors.HexColor('#92400E'),
         fontName='Helvetica', spaceAfter=6, spaceBefore=6, leading=14,
         leftIndent=10, backColor=colors.HexColor('#FFFBEB'), borderPadding=8)
TIP = S('TIP', fontSize=9.5, textColor=colors.HexColor('#065F46'),
        fontName='Helvetica', spaceAfter=6, spaceBefore=6, leading=14,
        leftIndent=10, backColor=GREEN_LIGHT, borderPadding=8)
TABLE_H = S('TABLE_H', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold',
            alignment=TA_CENTER, leading=13)
TABLE_C = S('TABLE_C', fontSize=9, textColor=DARK, fontName='Helvetica',
            alignment=TA_LEFT, leading=13)
TOC_CHAPTER = S('TOC_CHAPTER', fontSize=11, textColor=DARK, fontName='Helvetica-Bold',
                spaceAfter=3, spaceBefore=4, leading=15)
TOC_SECTION = S('TOC_SECTION', fontSize=10, textColor=GRAY, fontName='Helvetica',
                spaceAfter=2, spaceBefore=1, leading=14, leftIndent=14)
CHAPTER_LABEL = S('CHAPTER_LABEL', fontSize=11, textColor=GREEN, fontName='Helvetica-Bold',
                  spaceAfter=4, spaceBefore=0, leading=15)
COVER_SUBTITLE = S('COVER_SUBTITLE', fontSize=14, textColor=GRAY, fontName='Helvetica',
                   spaceAfter=8, spaceBefore=4, leading=20, alignment=TA_CENTER)
COVER_META = S('COVER_META', fontSize=10, textColor=GRAY, fontName='Helvetica',
               spaceAfter=4, spaceBefore=2, leading=15, alignment=TA_CENTER)


# ── Helpers ────────────────────────────────────────────────────────────────────
def p(text, style=BODY):
    return Paragraph(text, style)

def sp(h=0.3):
    return Spacer(1, h * cm)

def hr(color=GRAY_BORDER, thickness=0.5):
    return HRFlowable(width='100%', thickness=thickness, color=color, spaceAfter=8, spaceBefore=8)

def chapter_break(num, title):
    """Full page-break chapter opener."""
    return [
        PageBreak(),
        sp(0.5),
        p(f'Chapter {num}', CHAPTER_LABEL),
        p(title, H1),
        hr(GREEN, 2),
        sp(0.4),
    ]

def section(title):
    return p(title, H2)

def subsection(title):
    return p(title, H3)

def sub4(title):
    return p(title, H4)

def bullet(text):
    return p(f'• {text}', BULLET)

def bullets(*items):
    return [bullet(i) for i in items]

def note(text):
    return p(f'<b>Note:</b> {text}', NOTE)

def tip(text):
    return p(f'<b>Tip:</b> {text}', TIP)

def code(text):
    return p(text, CODE)

def info_table(rows, col_widths=None, header=True):
    """Renders a clean table. rows[0] is header if header=True."""
    if col_widths is None:
        col_widths = [CONTENT_W / len(rows[0])] * len(rows[0])

    data = []
    for i, row in enumerate(rows):
        if i == 0 and header:
            data.append([p(str(c), TABLE_H) for c in row])
        else:
            data.append([p(str(c), TABLE_C) for c in row])

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.4, GRAY_BORDER),
        ('BOX', (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])
    if not header:
        style.add('BACKGROUND', (0, 0), (-1, -1), WHITE)

    return Table(data, colWidths=col_widths, style=style, repeatRows=1)

def role_badge_text(role):
    return role.replace('_', ' ').title()


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT CONTENT
# ══════════════════════════════════════════════════════════════════════════════
def build_story():
    s = []

    # ─────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ─────────────────────────────────────────────────────────────────────────
    s += [
        sp(4),
        p('✈ Airfinder', S('cov', fontSize=42, textColor=GREEN,
                           fontName='Helvetica-Bold', alignment=TA_CENTER, leading=50)),
        sp(0.4),
        p('Complete Project Documentation', COVER_SUBTITLE),
        sp(0.2),
        hr(GREEN, 2),
        sp(0.6),
        p('A comprehensive guide for beginners, staff, and technical teams', COVER_META),
        sp(0.3),
        p(f'Version 1.0  ·  {datetime.date.today().strftime("%B %Y")}  ·  Confidential', COVER_META),
        sp(6),
        info_table(
            [['Document', 'Airfinder Project Documentation'],
             ['Version', '1.0'],
             ['Date', datetime.date.today().strftime('%d %B %Y')],
             ['Classification', 'Internal — Confidential'],
             ['Prepared by', 'Airfinder Engineering Team'],
             ['Audience', 'All staff, new joiners, technical team']],
            col_widths=[5 * cm, CONTENT_W - 5 * cm],
            header=False,
        ),
        PageBreak(),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # TABLE OF CONTENTS
    # ─────────────────────────────────────────────────────────────────────────
    s += [
        sp(0.5),
        p('Table of Contents', H1),
        hr(GREEN, 2),
        sp(0.4),
    ]
    toc = [
        ('1', 'Introduction & Project Overview', [
            'What is Airfinder?', 'Who is this for?', 'Key Features at a Glance',
        ]),
        ('2', 'Getting Started — For New Joiners', [
            'How to Access the System', 'Logging In', 'Navigating the Staff Portal',
            'Your First Day Checklist',
        ]),
        ('3', 'Customer-Facing Product Guide', [
            'The Homepage', 'Searching for Flights', 'AI-Powered Search',
            'Multi-City Search', 'Flight Results Page', 'Booking a Flight',
            'Multi-City Booking', 'Booking Confirmation & Email',
            'Flight Status Tracker', 'Customer Account',
        ]),
        ('4', 'Staff Portal — User & Account Management', [
            'Staff Roles Explained', 'Logging into the Staff Portal',
            'Dashboard Overview', 'Managing Staff Accounts',
            'Managing Customer Accounts', 'Managing Bookings',
            'Finance & Revenue Reports',
        ]),
        ('5', 'System Architecture & Technical Reference', [
            'Technology Stack', 'Project File Structure',
            'Database Models', 'API Reference',
            'Authentication & Security', 'Pricing Engine',
            'Flight Search Engine', 'Email Service',
        ]),
        ('6', 'Setup & Deployment Guide', [
            'Prerequisites', 'Local Development Setup',
            'Environment Variables', 'Database Initialisation',
            'Running the Server', 'Production Deployment (Render)',
            'Gmail SMTP Configuration',
        ]),
        ('7', 'Security & Compliance', [
            'Rate Limiting', 'JWT Token Security',
            'Password Policy', 'Role-Based Access Control',
            'Security Logging', 'CORS Policy',
        ]),
        ('8', 'Troubleshooting & FAQs', [
            'Common Login Issues', 'Booking Errors',
            'Server Startup Problems', 'Email Not Sending',
            'Frequently Asked Questions',
        ]),
    ]
    for num, title, subs in toc:
        s.append(p(f'{num}.  {title}', TOC_CHAPTER))
        for sub in subs:
            s.append(p(f'     ›  {sub}', TOC_SECTION))
        s.append(sp(0.15))
    s.append(PageBreak())

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 1 — INTRODUCTION
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(1, 'Introduction & Project Overview')

    s.append(section('1.1  What is Airfinder?'))
    s.append(p(
        'Airfinder is a full-featured flight booking and travel management platform built '
        'for travel agencies and corporate travel teams. It allows customers to search, '
        'compare, and book flights across 191 airports worldwide, while giving staff a '
        'powerful back-office portal to manage bookings, customers, revenue, and team '
        'accounts — all in one place.'
    ))
    s.append(p(
        'The platform is live at <b>http://localhost:5000</b> in development and can be '
        'deployed to Render or any cloud provider for production use.'
    ))

    s.append(section('1.2  Who is this Document For?'))
    s += [
        info_table([
            ['Audience', 'What They Will Find'],
            ['New joiners & beginners', 'Plain-English walkthrough of every feature and page, no technical knowledge needed'],
            ['Customer support staff', 'How to help customers with bookings, accounts, and flight status'],
            ['Administrators & agents', 'How to manage staff, customers, bookings, and the system day-to-day'],
            ['Finance staff', 'Revenue reports, commission tracking, pricing overview'],
            ['Developers & IT', 'Architecture, API reference, deployment, and configuration guide'],
        ], col_widths=[5.5 * cm, CONTENT_W - 5.5 * cm]),
        sp(0.3),
    ]

    s.append(section('1.3  Key Features at a Glance'))
    s += bullets(
        'Flight search across 191 airports and 50 airlines with accurate Haversine-based duration estimates',
        'AI-powered natural language search — type "flight from Lagos to London next month" and it understands',
        'Multi-city itinerary builder — up to 6 legs in a single booking session',
        'Flexible dates grid — compare prices across a 7-day window',
        'Real-time price lock countdown and seat urgency indicators during booking',
        'Flight status tracker with deterministic mock data (gate, terminal, delay, progress bar)',
        'Branded booking confirmation emails with full itinerary details',
        'Staff portal with role-based access (Super Admin, Admin, Agent, Finance)',
        'Staff account management: create, edit, delete, force password change on first login',
        'Revenue dashboard: total revenue, commissions, service fees, booking counts',
        'JWT authentication with bcrypt password hashing for customers and staff',
        'Rate limiting on all public endpoints to prevent abuse',
        'Security event logging for failed logins and suspicious activity',
        'EUR currency display throughout (converted client-side)',
        'Fully responsive — works on desktop, tablet, and mobile',
    )

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 2 — GETTING STARTED
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(2, 'Getting Started — For New Joiners')

    s.append(p(
        'Welcome to the team! This chapter is written for people who are new to Airfinder. '
        'You do not need any technical background to follow along. By the end of this chapter '
        'you will know how to log in, find your way around the staff portal, and help your first customer.'
    ))

    s.append(section('2.1  How to Access the System'))
    s.append(p(
        'Airfinder runs as a web application. You access it through your web browser — '
        'Google Chrome or Microsoft Edge are recommended. Your system administrator will '
        'give you the web address (URL) to use. In development and internal testing the '
        'address is:'
    ))
    s.append(code('http://localhost:5000'))
    s.append(p(
        'If you are accessing a live production version, you will be given a different URL '
        'by your administrator. Always use the URL you were given — do not guess or modify it.'
    ))

    s.append(section('2.2  Logging In'))
    s.append(p(
        'There are two separate login pages — one for customers (the public) and one for staff. '
        'As a staff member you must always use the <b>Staff Portal login</b>.'
    ))
    s += [
        info_table([
            ['Who', 'Login Page', 'URL'],
            ['Customers', 'Customer Login', '/auth/login.html'],
            ['All Staff', 'Staff Portal Login', '/admin/login.html'],
        ], col_widths=[3.5 * cm, 5 * cm, CONTENT_W - 8.5 * cm]),
        sp(0.3),
        subsection('First-Time Login'),
        p(
            'When your account is created by an administrator, you will receive an email containing '
            'a temporary password. On your very first login, the system will immediately redirect '
            'you to a <b>Change Password</b> page. This is mandatory — you cannot use any other '
            'part of the portal until you set your own password. Your new password must be at least '
            '8 characters long.'
        ),
        note('If you try to navigate directly to the dashboard before changing your password, '
             'the system will redirect you back to the change-password page automatically. '
             'This is a security feature, not a bug.'),
        sp(0.2),
        subsection('Forgot Your Password?'),
        p(
            'On the staff login page, click <b>Forgot Password</b>. Enter your email address. '
            'If the email is registered, you will receive a reset link valid for 1 hour. '
            'If email is not configured, the reset link will be shown directly on the page — '
            'copy it and open it in your browser.'
        ),
    ]

    s.append(section('2.3  Navigating the Staff Portal'))
    s.append(p(
        'After logging in you will see the main dashboard. On the left side is the navigation '
        'sidebar. The items you can see depend on your role — not all staff see all menu items.'
    ))
    s += [
        info_table([
            ['Sidebar Item', 'What It Does', 'Who Can See It'],
            ['Dashboard', 'Overview of bookings, revenue, and customers', 'All staff'],
            ['Bookings', 'View and manage all customer bookings', 'All staff'],
            ['Customers', 'View customer accounts and their history', 'Super Admin, Admin, Agent'],
            ['Staff', 'Create and manage staff accounts', 'Super Admin, Admin'],
            ['Finance', 'Revenue reports and commission summaries', 'Super Admin, Admin, Finance'],
            ['Settings', 'System configuration', 'Super Admin only'],
        ], col_widths=[4 * cm, 7.5 * cm, CONTENT_W - 11.5 * cm]),
        sp(0.3),
    ]
    s.append(note(
        'If you do not see a menu item listed above, it means your role does not have '
        'permission to access it. Contact your Super Admin if you believe you need access.'
    ))

    s.append(section('2.4  Your First Day Checklist'))
    s += [
        info_table([
            ['#', 'Task', 'Done?'],
            ['1', 'Log in to the Staff Portal at /admin/login.html', '☐'],
            ['2', 'Change your temporary password when prompted', '☐'],
            ['3', 'Confirm your name and role appear correctly in the sidebar', '☐'],
            ['4', 'Review the Dashboard — note total bookings and revenue', '☐'],
            ['5', 'Open the Bookings page and view a recent booking', '☐'],
            ['6', 'Ask your manager which tasks are assigned to your role', '☐'],
            ['7', 'Note the customer login URL to share with customers if needed', '☐'],
        ], col_widths=[1 * cm, CONTENT_W - 3 * cm, 2 * cm]),
        sp(0.3),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 3 — CUSTOMER-FACING PRODUCT
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(3, 'Customer-Facing Product Guide')

    s.append(p(
        'This chapter walks through every part of the website that customers interact with. '
        'Understanding the customer journey is essential for support staff — you need to '
        'know exactly what a customer sees and does so you can help them effectively.'
    ))

    s.append(section('3.1  The Homepage  (/)'))
    s.append(p(
        'The homepage is the first thing customers see. It has a large search form at the centre '
        'with tabs for three search types: <b>One Way</b>, <b>Round Trip</b>, and <b>Multi-City</b>. '
        'Below the search form, the page shows <b>Popular Routes</b> — real live prices pulled '
        'dynamically from the search engine. These routes include Lagos–London, Dubai–Tokyo, '
        'New York–Paris, and many more, and the prices update every time the page loads.'
    ))
    s.append(p(
        'The navbar at the top has links to Flight Status, Login, and Register. Logged-in '
        'customers also see a link to their Account Dashboard.'
    ))

    s.append(section('3.2  Standard Flight Search'))
    s += [
        subsection('How to Search'),
        p('Customers fill in the search form with the following fields:'),
        info_table([
            ['Field', 'Description', 'Required?'],
            ['From', 'Departure airport — type 3-letter IATA code or city name', 'Yes'],
            ['To', 'Arrival airport — type 3-letter IATA code or city name', 'Yes'],
            ['Departure Date', 'Date of travel in YYYY-MM-DD format', 'Yes'],
            ['Return Date', 'For round trips — optional', 'No'],
            ['Passengers', 'Number of passengers, 1–9', 'Yes'],
            ['Cabin Class', 'Economy, Business, or First', 'Yes'],
        ], col_widths=[3 * cm, CONTENT_W - 5.5 * cm, 2.5 * cm]),
        sp(0.3),
        p(
            'After clicking <b>Search Flights</b>, they are taken to the <b>Results Page</b>. '
            'Searches are rate-limited to 60 per minute per IP to prevent abuse.'
        ),
    ]

    s.append(section('3.3  AI-Powered Natural Language Search'))
    s.append(p(
        'Customers can describe their trip in plain English instead of filling in form fields. '
        'They click the <b>AI Search</b> button on the homepage and type something like:'
    ))
    s += [
        code('"I need a flight from Lagos to London next month for 2 people in business class"'),
        code('"Cheapest flight Lagos to Dubai under $800"'),
        code('"Flight from Abuja to Paris on July 15"'),
        sp(0.2),
        p(
            'The AI search parser extracts the origin, destination, date, passenger count, '
            'cabin class, and optional budget from the natural language query, then runs a '
            'normal flight search with those parameters. AI search is limited to 30 requests '
            'per minute.'
        ),
        tip('If a customer says the AI search did not work, ask them to be more specific about '
            'the city names and include a date. Ambiguous queries like "fly somewhere warm" '
            'will not produce results.'),
    ]

    s.append(section('3.4  Multi-City Search'))
    s.append(p(
        'The Multi-City tab on the homepage allows customers to plan trips with up to 6 separate '
        'flight legs. For example: Lagos → London → Paris → New York. Each leg has its own '
        'origin, destination, and date. After searching, each leg shows its own list of available '
        'flights.'
    ))

    s.append(section('3.5  Flight Results Page  (/results.html)'))
    s += [
        p(
            'The results page shows all available flights for the searched route and date. '
            'Each result card shows the airline, flight number, departure and arrival times, '
            'duration, cabin class, and total price in EUR.'
        ),
        subsection('Live Features on Results'),
        bullets(
            '<b>Live timestamp</b>: Shows when the results were last fetched',
            '<b>Auto-refresh</b>: Results refresh automatically every 5 minutes',
            '<b>Price filter</b>: Customers can filter results by maximum budget',
            '<b>Flexible dates grid</b>: Shows the cheapest price for ±3 days around the searched date',
            '<b>Sort options</b>: Sort by price or departure time',
        ),
        sp(0.2),
        subsection('Urgency Indicators'),
        p(
            'To assist with purchasing decisions, the results page shows:'
        ),
        bullets(
            '<b>Price lock countdown</b>: A 10-minute timer that indicates how long the displayed price is considered valid',
            '<b>Seat urgency</b>: A warning if fewer than 5 seats appear available at that price',
        ),
        note(
            'These indicators are for user experience purposes. The underlying flight data is '
            'generated by a deterministic mock engine — prices shown are consistent for the same '
            'route and date combination.'
        ),
    ]

    s.append(section('3.6  Booking a Flight  (/booking.html)'))
    s.append(p(
        'When a customer clicks <b>Book Now</b> on a result card, they are taken to the '
        'booking page. If they are not logged in, they will be redirected to login first. '
        'The booking page has three steps:'
    ))
    s += [
        info_table([
            ['Step', 'What Happens'],
            ['1. Passenger Details', 'Customer enters first name, last name, date of birth, passport number, and nationality for each passenger'],
            ['2. Extras', 'Customer selects baggage option (carry-on free, 1 checked bag +€32, 2 checked bags +€55) and seat preference (standard free, window +€14, aisle +€9, extra legroom +€41, front row +€28)'],
            ['3. Review & Pay', 'Customer sees full price breakdown and clicks Confirm Booking'],
        ], col_widths=[4 * cm, CONTENT_W - 4 * cm]),
        sp(0.3),
        p('On confirmation, a booking reference is generated (format: <b>AF</b> + 8 alphanumeric characters, e.g. AFYNLTZG20).'),
    ]

    s.append(section('3.7  Multi-City Booking  (/multicity.html)'))
    s.append(p(
        'After a multi-city search, the customer sees results for each leg. They select one '
        'flight per leg, then click <b>Book All Legs</b>. The booking creates one booking '
        'record per leg, all linked by a shared <b>Group Reference</b>. A single '
        'confirmation email shows all legs together.'
    ))

    s.append(section('3.8  Booking Confirmation & Email'))
    s += [
        p(
            'After a successful booking, the customer is taken to the <b>Confirmation Page</b> '
            '(/confirmation.html) which displays their booking reference, flight details, '
            'passenger list, and price breakdown.'
        ),
        p(
            'Simultaneously, the system sends a branded <b>HTML confirmation email</b> to the '
            "customer's registered email address. The email contains:"
        ),
        bullets(
            'Booking reference number',
            'Full flight details (route, airline, flight number, date, cabin class)',
            'Passenger names',
            'Itemised price breakdown (base fare, markup, service fee, baggage, seat)',
            'Total amount paid in EUR',
        ),
        p(
            'For multi-city bookings, the email shows all legs with a combined total and a '
            'single group reference for the entire itinerary.'
        ),
        note(
            'If MAIL_PASSWORD is not configured in the server environment, emails are written '
            'to a local log file instead of being sent. Confirm with your administrator whether '
            'live email is enabled.'
        ),
    ]

    s.append(section('3.9  Flight Status Tracker  (/flight-status.html)'))
    s.append(p(
        'Customers (and staff) can look up the real-time status of any flight by entering '
        'the flight number and travel date. The tracker shows:'
    ))
    s += [
        bullets(
            'Current status: On Time / Delayed / Boarding / Departed / Arrived / Cancelled',
            'Gate and terminal information',
            'Scheduled and actual departure/arrival times',
            'Delay duration in minutes (if delayed)',
            'Aircraft type',
            'Baggage belt number (if arrived)',
            '4-step visual progress bar',
            'Route with origin and destination city names',
        ),
        sp(0.2),
        p(
            'The page also includes 8 quick-lookup examples so customers can try it immediately. '
            'The tracker supports URL parameters: <b>?flight=LH401&date=2026-06-24</b> — '
            'useful for sharing a specific flight status link.'
        ),
        note(
            'Flight status data is deterministic mock data — the same flight number and date '
            'always returns the same status. This ensures a consistent experience while the '
            'platform is not yet connected to a live airline data feed.'
        ),
    ]

    s.append(section('3.10  Customer Account'))
    s += [
        p('Registered customers have access to three account pages:'),
        info_table([
            ['Page', 'URL', 'What It Contains'],
            ['Dashboard', '/account/dashboard.html', 'Welcome message, booking count, recent bookings, quick links'],
            ['My Bookings', '/account/bookings.html', 'Full list of all bookings with reference, route, date, status, and price'],
            ['Profile', '/account/profile.html', 'Update name, phone number, and change password'],
        ], col_widths=[3 * cm, 5.5 * cm, CONTENT_W - 8.5 * cm]),
        sp(0.3),
        p('Customers can cancel a booking from the My Bookings page. Cancelled bookings remain '
          'visible in the list with a "cancelled" status.'),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 4 — STAFF PORTAL
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(4, 'Staff Portal — User & Account Management')

    s.append(p(
        'The Staff Portal is the back-office control centre for Airfinder. This chapter '
        'covers every function available to staff, with step-by-step instructions for '
        'common support and management tasks.'
    ))

    s.append(section('4.1  Staff Roles Explained'))
    s.append(p(
        'Airfinder uses a 4-level role hierarchy. Higher roles have all the permissions of '
        'lower roles, plus additional capabilities.'
    ))
    s += [
        info_table([
            ['Role', 'Level', 'Key Permissions'],
            ['Super Admin', '4 (Highest)', 'Full access. Create/edit/delete any staff. Access all data. System settings.'],
            ['Admin', '3', 'Create and manage agents and finance staff. View all bookings and customers. Cannot delete staff.'],
            ['Agent', '2', 'View bookings and customers. Update booking status. Cannot manage staff.'],
            ['Finance', '1 (Lowest)', 'View Dashboard and Bookings. Access Finance revenue reports only. No customer or staff management.'],
        ], col_widths=[3 * cm, 2.5 * cm, CONTENT_W - 5.5 * cm]),
        sp(0.3),
        note(
            'A staff member can only manage accounts with a lower role than their own. '
            'An Admin cannot create or edit another Admin. Only a Super Admin can manage Admins.'
        ),
    ]

    s.append(section('4.2  Logging into the Staff Portal'))
    s += [
        p('Navigate to <b>/admin/login.html</b> and enter your email and password.'),
        p('Staff JWT tokens expire after <b>12 hours</b>. If you are redirected to the login '
          'page mid-session, your session has expired — simply log in again.'),
        subsection('Default Super Admin Credentials'),
        info_table([
            ['Email', 'admin@airfinder.com'],
            ['Password', 'Admin@2024!'],
        ], col_widths=[5 * cm, CONTENT_W - 5 * cm], header=False),
        sp(0.2),
        note(
            'Change the default Super Admin password immediately in any production environment. '
            'The default credentials are publicly known and must not be used on live systems.'
        ),
    ]

    s.append(section('4.3  Dashboard Overview  (/admin/dashboard.html)'))
    s.append(p('The dashboard shows four headline stat cards and two data tables.'))
    s += [
        info_table([
            ['Stat Card', 'What It Shows', 'Who Sees It'],
            ['Total Bookings', 'All bookings ever created', 'All staff'],
            ['Confirmed', 'Bookings with confirmed status', 'All staff'],
            ['Total Revenue', 'Sum of all confirmed booking totals in EUR', 'All staff'],
            ['Total Customers', 'Count of all registered customer accounts', 'All staff'],
            ['Staff Members', 'Total active staff accounts', 'Super Admin, Admin only'],
        ], col_widths=[4 * cm, 6.5 * cm, CONTENT_W - 10.5 * cm]),
        sp(0.3),
        p('The <b>Recent Bookings</b> table shows the 8 most recent bookings with reference, '
          'route, total, and status. Click <b>View All</b> to go to the full bookings list.'),
        p('The <b>Recent Customers</b> table shows the 8 most recently registered customers. '
          'This is only visible to Super Admin, Admin, and Agent roles — Finance staff see '
          'only the stat cards and recent bookings.'),
    ]

    s.append(section('4.4  Managing Staff Accounts  (/admin/staff.html)'))
    s.append(p('Available to: <b>Super Admin</b> and <b>Admin</b>.'))

    s.append(subsection('4.4.1  Creating a New Staff Account'))
    s += [
        p('Click <b>+ Add Staff Member</b> in the top-right of the Staff page. Fill in the form:'),
        info_table([
            ['Field', 'Notes'],
            ['First Name', 'Required'],
            ['Last Name', 'Required'],
            ['Email', 'Must be unique. Staff will log in with this email'],
            ['Role', 'Select from: Agent, Finance (Admin can assign these). Super Admin can also assign Admin'],
            ['Status', 'Active or Inactive'],
            ['Temporary Password', 'Optional — if left blank, a 12-character random password is generated automatically'],
        ], col_widths=[4.5 * cm, CONTENT_W - 4.5 * cm]),
        sp(0.2),
        p('After clicking <b>Create Staff</b>, a success panel shows the email address and '
          'temporary password. <b>Copy this immediately</b> — it is shown only once. A credentials '
          'email is also sent to the new staff member.'),
        p('The new account has <b>must_change_password = True</b> set automatically. The staff '
          'member will be forced to change their password on first login.'),
    ]

    s.append(subsection('4.4.2  Editing a Staff Account'))
    s += [
        p('Click the <b>Edit</b> button on any staff row. The edit modal pre-fills all current '
          'values. You can update:'),
        bullets(
            'First name and last name',
            'Email address (must be unique)',
            'Role (subject to your own role level)',
            'Status (Active / Inactive) — inactive staff cannot log in',
        ),
        p('Click <b>Save Changes</b>. The table updates immediately with a green confirmation toast.'),
    ]

    s.append(subsection('4.4.3  Resetting a Staff Password'))
    s += [
        p('Click <b>Reset PW</b> on any staff row. A new 12-character random temporary password '
          'is generated, the staff account is flagged for password change on next login, and a '
          'credentials email is sent. The new temporary password is also shown in a toast '
          'notification on screen.'),
        tip('Use password reset when a staff member is locked out or has forgotten their password.'),
    ]

    s.append(subsection('4.4.4  Deleting a Staff Account'))
    s += [
        p('<b>Super Admin only.</b> Click the <b>Delete</b> button (red) on a staff row. '
          'A confirmation dialog will appear. Confirm to permanently delete the account. '
          'This action cannot be undone.'),
        note('A Super Admin cannot delete their own account — the backend rejects this with '
             '"Cannot delete your own account".'),
    ]

    s.append(subsection('4.4.5  Deactivating vs. Deleting'))
    s += [
        info_table([
            ['Action', 'Effect', 'When to Use'],
            ['Deactivate (set Inactive)', 'Staff cannot log in but account and history preserved', 'Temporary leave, role change, pending review'],
            ['Delete', 'Account permanently removed from database', 'Account no longer needed, data cleanup'],
        ], col_widths=[4.5 * cm, 5.5 * cm, CONTENT_W - 10 * cm]),
        sp(0.3),
    ]

    s.append(section('4.5  Managing Customer Accounts  (/admin/customers.html)'))
    s.append(p('Available to: <b>Super Admin</b>, <b>Admin</b>, <b>Agent</b>.'))
    s += [
        p('The Customers page lists all registered customer accounts with their name, email, '
          'registration date, booking count, and total spend.'),
        p('You can search customers by name or email using the search bar at the top.'),
        subsection('Common Support Tasks'),
        info_table([
            ['Task', 'How to Do It'],
            ['Find a customer account', 'Use the search bar with their name or email'],
            ['See all bookings for a customer', 'Click on the customer row to view their booking history'],
            ['Check if account is active', 'Look at the Status column — Active = green badge, Inactive = grey'],
        ], col_widths=[5 * cm, CONTENT_W - 5 * cm]),
        sp(0.3),
    ]

    s.append(section('4.6  Managing Bookings  (/admin/bookings.html)'))
    s += [
        p('All staff can view the bookings list. Agents and above can update booking status.'),
        subsection('Booking Status Values'),
        info_table([
            ['Status', 'Meaning', 'Badge Colour'],
            ['Confirmed', 'Booking is active and paid', 'Green'],
            ['Pending', 'Booking created but not yet confirmed', 'Amber'],
            ['Cancelled', 'Booking was cancelled by customer or staff', 'Red'],
            ['Refunded', 'Booking has been refunded', 'Blue'],
        ], col_widths=[3 * cm, 7 * cm, CONTENT_W - 10 * cm]),
        sp(0.3),
        subsection('Changing a Booking Status'),
        p('Open a booking by clicking on its row. In the detail view, use the Status dropdown '
          'to change the status and click Save. The change is recorded immediately.'),
        subsection('Multi-City Bookings'),
        p('Multi-city bookings have a <b>Group Reference</b> that links all legs together. '
          'In the bookings list, legs are shown individually but share the same group reference. '
          'When filtering or searching, you can search by the group reference to see all legs of '
          'a multi-city itinerary.'),
    ]

    s.append(section('4.7  Finance & Revenue Reports  (/admin/finance.html)'))
    s.append(p('Available to: <b>Super Admin</b>, <b>Admin</b>, <b>Finance</b>.'))
    s += [
        p('The Finance page provides a revenue summary including:'),
        bullets(
            'Total revenue from all confirmed bookings',
            'Total commissions earned (3% of base fare by default)',
            'Total service fees collected (€15 per booking by default)',
            'Monthly revenue breakdown chart',
            'Booking count by status',
        ),
        sp(0.2),
        subsection('Revenue Configuration'),
        p('Revenue calculations use these configurable rates (set in .env):'),
        info_table([
            ['Setting', 'Default Value', 'Description'],
            ['DEFAULT_MARKUP_PERCENT', '8%', 'Markup added on top of base fare'],
            ['DEFAULT_SERVICE_FEE_USD', '$15', 'Flat fee per booking'],
            ['DEFAULT_COMMISSION_PERCENT', '3%', 'Commission on base fare (agency income)'],
        ], col_widths=[5.5 * cm, 3 * cm, CONTENT_W - 8.5 * cm]),
        sp(0.3),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 5 — ARCHITECTURE & TECHNICAL REFERENCE
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(5, 'System Architecture & Technical Reference')

    s.append(p(
        'This chapter is written for developers and technical staff. It covers the technology '
        'stack, codebase structure, database models, and API reference.'
    ))

    s.append(section('5.1  Technology Stack'))
    s += [
        info_table([
            ['Layer', 'Technology', 'Version / Notes'],
            ['Backend Framework', 'Python Flask', '3.0.3'],
            ['Database', 'SQLite (dev) / PostgreSQL (prod)', 'Via SQLAlchemy 3.1.1'],
            ['ORM', 'Flask-SQLAlchemy', '3.1.1'],
            ['Authentication', 'PyJWT + bcrypt', 'JWT HS256, bcrypt hashing'],
            ['Email', 'Flask-Mail + Gmail SMTP', 'TLS port 587'],
            ['Rate Limiting', 'Flask-Limiter', '3.8.0'],
            ['CORS', 'Flask-CORS', '4.0.1'],
            ['Frontend', 'Vanilla HTML / CSS / JavaScript', 'No framework, CommonJS modules'],
            ['Fonts', 'Inter (Google Fonts)', 'Loaded from CDN'],
            ['Production Server', 'Gunicorn', '22.0.0'],
            ['Deployment', 'Render', 'render.yaml configuration'],
        ], col_widths=[4 * cm, 5 * cm, CONTENT_W - 9 * cm]),
        sp(0.3),
    ]

    s.append(section('5.2  Project File Structure'))
    s += [
        code('Airfinder/'),
        code('├── backend/                  # All Python server code'),
        code('│   ├── app.py                # Flask app factory + route mounting'),
        code('│   ├── config.py             # All config from .env'),
        code('│   ├── extensions.py         # Flask-Limiter, Flask-Mail instances'),
        code('│   ├── middleware/'),
        code('│   │   ├── jwt_guard.py      # JWT decode decorators'),
        code('│   │   └── role_guard.py     # Role-based access decorator'),
        code('│   ├── models/'),
        code('│   │   ├── database.py       # SQLAlchemy db instance + init_db()'),
        code('│   │   ├── user.py           # Customer User model'),
        code('│   │   ├── staff.py          # Staff model + StaffRole enum'),
        code('│   │   └── booking.py        # Booking model + BookingStatus enum'),
        code('│   ├── routes/'),
        code('│   │   ├── auth_customer.py  # Customer register/login/reset/profile'),
        code('│   │   ├── auth_staff.py     # Staff login/change-password/reset'),
        code('│   │   ├── flights.py        # Search, AI search, multicity, status'),
        code('│   │   ├── bookings.py       # Create/view/cancel bookings'),
        code('│   │   ├── admin.py          # Dashboard, customer list, booking mgmt'),
        code('│   │   └── staff_mgmt.py     # Staff CRUD (create/edit/delete/reset)'),
        code('│   └── services/'),
        code('│       ├── mock_flights.py   # 191-airport flight search engine'),
        code('│       ├── ai_search.py      # Natural language query parser'),
        code('│       ├── pricing.py        # Fare calculation with markup/fees'),
        code('│       ├── email_service.py  # HTML email templates + send functions'),
        code('│       └── security_logger.py# Failed login / security event logging'),
        code('├── frontend/                 # All HTML/CSS/JS (served by Flask)'),
        code('│   ├── index.html            # Homepage'),
        code('│   ├── results.html          # Search results'),
        code('│   ├── booking.html          # Booking flow'),
        code('│   ├── confirmation.html     # Booking confirmed'),
        code('│   ├── multicity.html        # Multi-city results + booking'),
        code('│   ├── flight-status.html    # Flight tracker'),
        code('│   ├── auth/                 # Customer auth pages'),
        code('│   ├── account/              # Customer account pages'),
        code('│   ├── admin/                # Staff portal pages'),
        code('│   ├── css/                  # main.css, admin.css, components.css, search.css'),
        code('│   └── js/                   # api.js, auth.js, admin.js, locale.js, search.js'),
        code('├── .env                      # Environment variables (never commit)'),
        code('├── requirements.txt          # Python dependencies'),
        code('├── render.yaml               # Render deployment config'),
        code('└── run.py                    # Entry point (imports create_app)'),
        sp(0.3),
    ]

    s.append(section('5.3  Database Models'))

    s.append(subsection('5.3.1  User (customers)'))
    s += [
        info_table([
            ['Column', 'Type', 'Description'],
            ['id', 'String(36)', 'UUID primary key'],
            ['email', 'String(255)', 'Unique, indexed, lowercase'],
            ['password_hash', 'String(255)', 'bcrypt hash'],
            ['first_name / last_name', 'String(100)', 'Customer name'],
            ['phone', 'String(30)', 'Optional phone number'],
            ['is_active', 'Boolean', 'False = cannot log in'],
            ['is_verified', 'Boolean', 'Email verification flag (auto-true in demo)'],
            ['reset_token', 'String(255)', 'Password reset token (urlsafe, 32 bytes)'],
            ['reset_token_expiry', 'DateTime', 'Token expires after 15 minutes'],
            ['created_at / updated_at', 'DateTime', 'Audit timestamps'],
        ], col_widths=[4.5 * cm, 3.5 * cm, CONTENT_W - 8 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.3.2  Staff'))
    s += [
        info_table([
            ['Column', 'Type', 'Description'],
            ['id', 'String(36)', 'UUID primary key'],
            ['email', 'String(255)', 'Unique, indexed, lowercase'],
            ['password_hash', 'String(255)', 'bcrypt hash'],
            ['first_name / last_name', 'String(100)', 'Staff name'],
            ['role', 'Enum(StaffRole)', 'super_admin / admin / agent / finance'],
            ['must_change_password', 'Boolean', 'True = forced to change PW on next login'],
            ['is_active', 'Boolean', 'False = cannot log in'],
            ['created_by', 'String(36)', 'FK to staff.id — who created this account'],
            ['last_login', 'DateTime', 'Recorded on each successful login'],
            ['reset_token', 'String(64)', 'Staff password reset token'],
            ['reset_token_expires', 'DateTime', 'Expires after 1 hour'],
        ], col_widths=[4.5 * cm, 3.5 * cm, CONTENT_W - 8 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.3.3  Booking'))
    s += [
        info_table([
            ['Column', 'Type', 'Description'],
            ['id', 'String(36)', 'UUID primary key'],
            ['reference', 'String(20)', 'Unique booking ref e.g. AFYNLTZG20'],
            ['user_id', 'String(36)', 'FK to users.id'],
            ['flight_id', 'String(100)', 'Flight identifier from search engine'],
            ['origin / destination', 'String(10)', 'IATA airport codes'],
            ['departure_date', 'String(20)', 'Date as stored at booking time'],
            ['airline / flight_number', 'String', 'Snapshot at booking time'],
            ['cabin_class', 'String(20)', 'economy / business / first'],
            ['passengers_json', 'Text', 'JSON array of passenger objects'],
            ['passenger_count', 'Integer', 'Count of passengers'],
            ['base_fare_usd', 'Float', 'Raw fare before markup'],
            ['markup_usd', 'Float', '8% markup (configurable)'],
            ['service_fee_usd', 'Float', '$15 flat fee (configurable)'],
            ['baggage_fee_usd / seat_fee_usd', 'Float', 'Optional add-on fees'],
            ['total_usd', 'Float', 'Final total paid'],
            ['commission_usd', 'Float', '3% of base fare (agency revenue)'],
            ['status', 'Enum(BookingStatus)', 'pending / confirmed / cancelled / refunded'],
            ['group_reference', 'String(20)', 'Links multi-city legs together'],
            ['is_multicity', 'Boolean', 'True for multi-city booking legs'],
        ], col_widths=[5 * cm, 3 * cm, CONTENT_W - 8 * cm]),
        sp(0.3),
    ]

    s.append(section('5.4  API Reference'))
    s.append(p('All API endpoints are prefixed with their blueprint URL. Authentication uses '
               '<b>Bearer token</b> in the Authorization header.'))

    s.append(subsection('5.4.1  Customer Authentication  (/api/auth)'))
    s += [
        info_table([
            ['Method', 'Endpoint', 'Auth', 'Description'],
            ['POST', '/register', 'None', 'Create customer account'],
            ['POST', '/login', 'None', 'Customer login → JWT token'],
            ['POST', '/forgot-password', 'None', 'Send password reset email'],
            ['POST', '/reset-password', 'None', 'Reset password with token'],
            ['GET', '/me', 'JWT', 'Get current customer profile'],
            ['PUT', '/me', 'JWT', 'Update name and phone'],
            ['POST', '/change-password', 'JWT', 'Change own password'],
        ], col_widths=[1.8 * cm, 4.5 * cm, 1.8 * cm, CONTENT_W - 8.1 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.4.2  Staff Authentication  (/api/staff/auth)'))
    s += [
        info_table([
            ['Method', 'Endpoint', 'Auth', 'Description'],
            ['POST', '/login', 'None', 'Staff login → 12h JWT token'],
            ['POST', '/change-password', 'JWT', 'Change temp password (bypasses must_change_password guard)'],
            ['GET', '/me', 'Staff JWT', 'Get current staff profile'],
            ['POST', '/forgot-password', 'None', 'Send reset link to staff email'],
            ['POST', '/reset-password', 'None', 'Reset with token (1h expiry)'],
        ], col_widths=[1.8 * cm, 4.5 * cm, 1.8 * cm, CONTENT_W - 8.1 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.4.3  Flight Search  (/api/flights)'))
    s += [
        info_table([
            ['Method', 'Endpoint', 'Rate Limit', 'Description'],
            ['GET', '/search', '60/min', 'Standard flight search (origin, destination, date, passengers, cabin, return_date, budget_max)'],
            ['POST', '/search/ai', '30/min', 'Natural language search — body: {query}'],
            ['POST', '/search/multicity', '20/min', 'Multi-leg search — body: {legs[], passengers, cabin}'],
            ['GET', '/search/flexible', '20/min', 'Price grid ±3 days around a date'],
            ['GET', '/featured', 'None', 'Popular routes with live prices'],
            ['GET', '/airports', 'None', 'Full list of 191 airports'],
            ['POST', '/pricing/calculate', '60/min', 'Calculate total for given base fare + options'],
            ['GET', '/pricing/options', 'None', 'Baggage and seat fee options'],
            ['GET', '/status', '60/min', 'Flight status by number + date'],
        ], col_widths=[1.8 * cm, 4.5 * cm, 2 * cm, CONTENT_W - 8.3 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.4.4  Bookings  (/api/bookings)'))
    s += [
        info_table([
            ['Method', 'Endpoint', 'Auth', 'Description'],
            ['POST', '/', 'JWT', 'Create single booking (10/min limit)'],
            ['POST', '/multicity', 'JWT', 'Create multi-city booking (5/min limit)'],
            ['GET', '/', 'JWT', 'List bookings (customers see own; staff see all)'],
            ['GET', '/<id>', 'JWT', 'Get single booking'],
            ['POST', '/<id>/cancel', 'JWT', 'Cancel a booking'],
        ], col_widths=[1.8 * cm, 4 * cm, 1.8 * cm, CONTENT_W - 7.6 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.4.5  Admin  (/api/admin)'))
    s += [
        info_table([
            ['Method', 'Endpoint', 'Role', 'Description'],
            ['GET', '/dashboard', 'All staff', 'Stats: bookings, revenue, customers, staff'],
            ['GET', '/customers', 'Admin+', 'Paginated customer list with search'],
            ['GET', '/bookings', 'All staff', 'Paginated booking list with status filter'],
            ['PUT', '/bookings/<id>', 'Agent+', 'Update booking status or notes'],
            ['GET', '/finance/summary', 'Finance+', 'Revenue summary and breakdown'],
        ], col_widths=[1.8 * cm, 4.5 * cm, 2.5 * cm, CONTENT_W - 8.8 * cm]),
        sp(0.3),
    ]

    s.append(subsection('5.4.6  Staff Management  (/api/admin/staff)'))
    s += [
        info_table([
            ['Method', 'Endpoint', 'Role', 'Description'],
            ['GET', '/', 'Admin+', 'List all staff accounts'],
            ['POST', '/', 'Admin+', 'Create staff (optional temp_password field)'],
            ['GET', '/<id>', 'Admin+', 'Get single staff account'],
            ['PUT', '/<id>', 'Admin+', 'Edit name, email, role, or status'],
            ['POST', '/<id>/reset-password', 'Admin+', 'Generate new temp password + email'],
            ['DELETE', '/<id>', 'Super Admin', 'Permanently delete staff account'],
        ], col_widths=[1.8 * cm, 4.5 * cm, 2.5 * cm, CONTENT_W - 8.8 * cm]),
        sp(0.3),
    ]

    s.append(section('5.5  Authentication & Security Architecture'))
    s += [
        subsection('JWT Token Design'),
        p('Both customers and staff authenticate with JSON Web Tokens (JWT). Tokens are '
          'HS256-signed with the JWT_SECRET from .env. Token payload:'),
        info_table([
            ['Claim', 'Type', 'Description'],
            ['user_id', 'String', 'UUID of the user or staff account'],
            ['role', 'String', 'customer / super_admin / admin / agent / finance'],
            ['must_change_password', 'Boolean', 'True = staff must change PW before other actions'],
            ['exp', 'Integer', 'Expiry: customers 24h, staff 12h'],
        ], col_widths=[4.5 * cm, 2.5 * cm, CONTENT_W - 7 * cm]),
        sp(0.3),
        subsection('Password Hashing'),
        p('All passwords are hashed with bcrypt before storage. The raw password is never '
          'stored and cannot be recovered — only verified with bcrypt.checkpw(). When a '
          'staff password is reset, a new bcrypt hash of the temporary password is stored.'),
        subsection('Role Guard'),
        p('The @require_role(*roles) decorator on backend routes verifies the JWT and '
          'checks the role claim. Requests with an insufficient role return HTTP 403.'),
    ]

    s.append(section('5.6  Pricing Engine  (backend/services/pricing.py)'))
    s += [
        p('Every booking total is calculated by the pricing engine. The formula:'),
        code('markup = base_fare × markup_pct / 100  (default 8%)'),
        code('baggage_fee = baggage_rate × passengers'),
        code('seat_fee = seat_rate × passengers'),
        code('subtotal_per_pax = base_fare + markup + service_fee + per_pax_baggage + per_pax_seat'),
        code('total = subtotal_per_pax × passengers'),
        code('commission = base_fare × commission_pct / 100  (default 3%)'),
        sp(0.2),
        info_table([
            ['Option', 'Fee per Passenger'],
            ['Carry-on baggage', '€0 (included)'],
            ['1 Checked bag', '+€32'],
            ['2 Checked bags', '+€55'],
            ['Standard seat', '€0 (included)'],
            ['Window seat', '+€14'],
            ['Aisle seat', '+€9'],
            ['Extra legroom', '+€41'],
            ['Front row', '+€28'],
        ], col_widths=[6 * cm, CONTENT_W - 6 * cm]),
        sp(0.3),
    ]

    s.append(section('5.7  Flight Search Engine  (backend/services/mock_flights.py)'))
    s += [
        p('The flight search engine generates realistic flight options for any route across '
          '191 airports and 50 airlines. Key features:'),
        bullets(
            '<b>Haversine formula</b>: Accurate great-circle distance between airports used to compute realistic flight durations',
            '<b>Deterministic seeding</b>: Same route + date always produces the same set of flights (uses hashlib.md5 seed)',
            '<b>Regional airline routing</b>: 6 regional airline pools; longhaul flag controls which airlines appear on cross-region routes',
            '<b>Airport carrier whitelist (AIRPORT_CARRIERS)</b>: Secondary airports like Port Harcourt (PHC) only show airlines that actually serve them',
            '<b>lru_cache on _estimate_duration</b>: Repeated duration lookups for the same route are cached in memory',
        ),
        sp(0.2),
        subsection('Airline Routing Logic'),
        p('When building the airline pool for a route:'),
        bullets(
            'Same region: only carriers from that region are eligible',
            'Cross-region: longhaul carriers from both regions + all Middle East carriers',
            'Fallback: if pool has fewer than 4 airlines, any longhaul airline is added',
            'AIRPORT_CARRIERS whitelist applied last — removes non-eligible airlines for restricted airports',
        ),
    ]

    s.append(section('5.8  Email Service  (backend/services/email_service.py)'))
    s += [
        p('The email service sends branded HTML emails for four events:'),
        info_table([
            ['Function', 'Trigger', 'Template'],
            ['send_welcome_email', 'Customer registers', 'Welcome + "Start Exploring" CTA'],
            ['send_booking_confirmation_email', 'Single booking confirmed', 'Flight details + itemised receipt'],
            ['send_multicity_confirmation_email', 'Multi-city booking confirmed', 'All legs listed + combined total'],
            ['send_staff_credentials_email', 'Staff created or password reset', 'Email + temporary password'],
        ], col_widths=[5.5 * cm, 4 * cm, CONTENT_W - 9.5 * cm]),
        sp(0.3),
        p('All emails share a consistent branded wrapper: green (#407E3C) header with the '
          'Airfinder logo, white content card, and "© 2026 Airfinder" footer.'),
        p('<b>Dev mode</b>: If MAIL_PASSWORD contains "your-" (i.e. is a placeholder), emails '
          'are written to <b>.claude/email_dev.log</b> instead of being sent. This prevents '
          'accidental sends during development.'),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 6 — SETUP & DEPLOYMENT
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(6, 'Setup & Deployment Guide')

    s.append(p(
        'This chapter covers everything needed to get Airfinder running from scratch, '
        'configure it for production, and deploy it to a cloud host.'
    ))

    s.append(section('6.1  Prerequisites'))
    s += [
        info_table([
            ['Requirement', 'Version', 'Notes'],
            ['Python', '3.10+', 'Earlier versions not tested'],
            ['pip', 'Latest', 'Comes with Python'],
            ['Git', 'Any', 'For cloning and version control'],
            ['Gmail account', 'Any', 'For SMTP email (or use any SMTP provider)'],
        ], col_widths=[4 * cm, 3 * cm, CONTENT_W - 7 * cm]),
        sp(0.3),
    ]

    s.append(section('6.2  Local Development Setup'))
    s += [
        p('<b>Step 1:</b> Clone the repository'),
        code('git clone https://github.com/Obinwanne1/Airfinder.git'),
        code('cd Airfinder'),
        sp(0.2),
        p('<b>Step 2:</b> Create and activate a Python virtual environment'),
        code('python -m venv venv'),
        code('venv\\Scripts\\activate        # Windows'),
        code('source venv/bin/activate       # Mac / Linux'),
        sp(0.2),
        p('<b>Step 3:</b> Install dependencies'),
        code('pip install -r requirements.txt'),
        sp(0.2),
        p('<b>Step 4:</b> Create the .env file (see Section 6.3)'),
        sp(0.2),
        p('<b>Step 5:</b> Run the server'),
        code('python -m backend.app'),
        sp(0.2),
        p('<b>Step 6:</b> Open in browser'),
        code('http://localhost:5000'),
        sp(0.3),
        note('On Windows, always use <b>python -m backend.app</b> (not python backend/app.py) '
             'to ensure the module paths resolve correctly. Set PYTHONPATH if needed: '
             '$env:PYTHONPATH = "C:\\path\\to\\Airfinder"'),
    ]

    s.append(section('6.3  Environment Variables  (.env)'))
    s.append(p('Create a file named <b>.env</b> in the project root. Never commit this file to git.'))
    s += [
        info_table([
            ['Variable', 'Example Value', 'Description'],
            ['SECRET_KEY', 'a-very-long-random-string', 'Flask session secret — use 32+ random chars'],
            ['JWT_SECRET', 'another-random-string', 'JWT signing key — use 32+ random chars'],
            ['DATABASE_URL', 'sqlite:///airfinder.db', 'SQLite for dev; postgresql:// for prod'],
            ['PORT', '5000', 'Server port'],
            ['MAIL_SERVER', 'smtp.gmail.com', 'SMTP host'],
            ['MAIL_PORT', '587', 'SMTP port (TLS)'],
            ['MAIL_USE_TLS', 'True', 'Always True for Gmail TLS'],
            ['MAIL_USERNAME', 'you@gmail.com', 'Gmail address'],
            ['MAIL_PASSWORD', 'xxxx xxxx xxxx xxxx', 'Gmail App Password (16 chars, spaces ok)'],
            ['MAIL_DEFAULT_SENDER', 'Airfinder <you@gmail.com>', 'From: header in emails'],
            ['DEFAULT_MARKUP_PERCENT', '8', 'Fare markup percentage'],
            ['DEFAULT_SERVICE_FEE_USD', '15', 'Flat service fee per booking'],
            ['DEFAULT_COMMISSION_PERCENT', '3', 'Commission on base fare'],
            ['SUPER_ADMIN_EMAIL', 'admin@airfinder.com', 'Auto-created super admin email'],
            ['SUPER_ADMIN_PASSWORD', 'Admin@2024!', 'Auto-created super admin password'],
            ['ALLOWED_ORIGINS', 'http://localhost:5000', 'CORS origins (comma-separated)'],
        ], col_widths=[5 * cm, 4 * cm, CONTENT_W - 9 * cm]),
        sp(0.3),
    ]

    s.append(section('6.4  Database Initialisation'))
    s += [
        p('The database is created automatically on first run. SQLAlchemy calls '
          'db.create_all() inside init_db() when the Flask app starts. '
          'The SQLite file is stored at <b>instance/airfinder.db</b>.'),
        p('To seed demo data (optional):'),
        code('python seed_demo.py'),
        p('To reset the super admin password if locked out:'),
        code('python reset_admin.py'),
        sp(0.3),
    ]

    s.append(section('6.5  Running the Server'))
    s += [
        subsection('Development (with auto-reload)'),
        code('python -m backend.app'),
        sp(0.15),
        subsection('Production with Gunicorn'),
        code('gunicorn "backend.app:create_app()" --bind 0.0.0.0:5000 --workers 4'),
        sp(0.3),
    ]

    s.append(section('6.6  Production Deployment on Render'))
    s += [
        p('The project includes a <b>render.yaml</b> file for one-click deployment on Render.'),
        bullets(
            'Push the repository to GitHub',
            'Create a new Web Service on Render and connect the GitHub repo',
            'Render reads render.yaml and configures build and start commands automatically',
            'Add all .env variables as Environment Variables in the Render dashboard',
            'For PostgreSQL: create a Render PostgreSQL database, copy the connection string, set DATABASE_URL',
            'Deploy — Render will install requirements and start Gunicorn',
        ),
        sp(0.2),
        note('Change SECRET_KEY and JWT_SECRET to long random strings in production. '
             'Never use the development defaults on a live server.'),
    ]

    s.append(section('6.7  Gmail SMTP Configuration'))
    s += [
        p('To send real emails, you need a Gmail App Password (not your regular Gmail password).'),
        p('<b>Steps to create a Gmail App Password:</b>'),
        info_table([
            ['Step', 'Action'],
            ['1', 'Go to myaccount.google.com → Security'],
            ['2', 'Enable 2-Step Verification if not already on'],
            ['3', 'Search for "App Passwords" in the search bar'],
            ['4', 'Select App: Mail, Device: Other → type "Airfinder" → Generate'],
            ['5', 'Copy the 16-character password shown (with or without spaces)'],
            ['6', 'Set MAIL_PASSWORD=xxxx xxxx xxxx xxxx in your .env file'],
            ['7', 'Restart the server — MAIL_PASSWORD change requires restart'],
        ], col_widths=[1 * cm, CONTENT_W - 1 * cm]),
        sp(0.2),
        tip('Gmail App Passwords look like: abcd efgh ijkl mnop. Spaces are fine in the .env value.'),
        note('Gmail has a daily sending limit of 500 emails for regular accounts. '
             'For high-volume production use, consider SendGrid, Mailgun, or AWS SES.'),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 7 — SECURITY
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(7, 'Security & Compliance')

    s.append(section('7.1  Rate Limiting'))
    s += [
        p('Flask-Limiter applies per-IP rate limits on all sensitive endpoints to prevent '
          'brute-force attacks and abuse:'),
        info_table([
            ['Endpoint', 'Limit'],
            ['Customer login', '10 per minute'],
            ['Staff login', '10 per minute'],
            ['Customer registration', '10 per hour'],
            ['Forgot password (customer)', '5 per hour'],
            ['Forgot password (staff)', '5 per minute'],
            ['AI search', '30 per minute'],
            ['Multi-city search', '20 per minute'],
            ['Standard flight search', '60 per minute'],
            ['Create booking', '10 per minute'],
            ['Create multi-city booking', '5 per minute'],
        ], col_widths=[8 * cm, CONTENT_W - 8 * cm]),
        sp(0.3),
    ]

    s.append(section('7.2  JWT Token Security'))
    s += [
        bullets(
            'All tokens are signed with HS256 using the JWT_SECRET environment variable',
            'Tokens are short-lived: 24 hours for customers, 12 hours for staff',
            'Tokens are stored in localStorage on the client (acceptable for internal tools; for public-facing apps, consider httpOnly cookies)',
            'Token claims include role and must_change_password — both checked on every protected route',
            'No token revocation mechanism currently — if a token must be invalidated immediately, the JWT_SECRET can be rotated (this logs everyone out)',
        ),
    ]

    s.append(section('7.3  Password Policy'))
    s += [
        info_table([
            ['Rule', 'Applies To'],
            ['Minimum 8 characters', 'All users and staff'],
            ['Cannot reuse current password when changing', 'All users and staff'],
            ['bcrypt hashing (work factor ≥ 12)', 'All stored passwords'],
            ['Temporary passwords are 12 chars with letters, digits, and symbols', 'Staff accounts'],
            ['Must change temporary password on first login', 'All staff accounts'],
            ['Password reset tokens expire in 15 min (customers) / 1 hour (staff)', 'Forgot password flow'],
        ], col_widths=[8 * cm, CONTENT_W - 8 * cm]),
        sp(0.3),
    ]

    s.append(section('7.4  Role-Based Access Control (RBAC)'))
    s += [
        p('Access control is enforced at two levels:'),
        p('<b>Backend (authoritative)</b>: The @require_role() decorator on every protected '
          'route verifies the JWT role claim server-side. No client-side check can bypass this.'),
        p('<b>Frontend (UX only)</b>: The data-role-only HTML attribute hides sidebar items '
          'and UI elements for unauthorised roles. This improves UX but is not a security boundary.'),
        note('Never rely on frontend role checks for security. The backend is the only '
             'authoritative access control layer.'),
    ]

    s.append(section('7.5  Security Event Logging'))
    s += [
        p('Failed authentication attempts are logged to <b>security.log</b> in the project root:'),
        code('{"event": "login_failed", "user_type": "customer", "email": "...", "ip": "...", "timestamp": "..."}'),
        p('Events logged:'),
        bullets(
            'login_failed — customer or staff login with wrong credentials',
            'password_change_failed — wrong current password provided',
        ),
        p('Review security.log regularly in production. Multiple failed login attempts '
          'from the same IP may indicate a brute-force attack (rate limiting will block '
          'most automated attacks, but manual review is still good practice).'),
    ]

    s.append(section('7.6  CORS Policy'))
    s += [
        p('Cross-Origin Resource Sharing is configured to allow API requests only from '
          'origins listed in ALLOWED_ORIGINS (.env). The default is localhost:5000 only.'),
        p('For production, update ALLOWED_ORIGINS to your actual domain:'),
        code('ALLOWED_ORIGINS=https://airfinder.yourdomain.com'),
        note('CORS only restricts browser-based requests. Direct API calls from tools like '
             'curl or Postman are not blocked by CORS — backend authentication is the real '
             'security boundary.'),
    ]

    # ─────────────────────────────────────────────────────────────────────────
    # CHAPTER 8 — TROUBLESHOOTING
    # ─────────────────────────────────────────────────────────────────────────
    s += chapter_break(8, 'Troubleshooting & FAQs')

    s.append(section('8.1  Common Login Issues'))
    s += [
        info_table([
            ['Symptom', 'Likely Cause', 'Fix'],
            ['"Invalid credentials"', 'Wrong email or password', 'Ask admin to reset password via Staff page → Reset PW button'],
            ['"Account deactivated"', 'is_active = False on the account', 'Admin sets Status to Active in Edit modal'],
            ['Redirected to change-password immediately', 'must_change_password = True', 'Normal — change the temporary password to proceed'],
            ['Session expired mid-use', 'Staff token expired (12h limit)', 'Log out and log back in'],
            ['Login page loops (redirects back)', 'Must_change_password and navigating away from change-password page', 'Complete the password change — do not navigate away'],
        ], col_widths=[4 * cm, 4.5 * cm, CONTENT_W - 8.5 * cm]),
        sp(0.3),
    ]

    s.append(section('8.2  Booking Errors'))
    s += [
        info_table([
            ['Error', 'Cause', 'Fix'],
            ['"Required fields: ..."', 'Frontend did not send all required booking fields', 'Reload the booking page and try again'],
            ['Booking created but no email', 'MAIL_PASSWORD is a placeholder', 'Configure Gmail App Password in .env and restart server'],
            ['Duplicate reference collision (very rare)', 'Random reference already exists', 'The system auto-retries — this resolves itself'],
        ], col_widths=[4 * cm, 4.5 * cm, CONTENT_W - 8.5 * cm]),
        sp(0.3),
    ]

    s.append(section('8.3  Server Startup Problems'))
    s += [
        info_table([
            ['Error', 'Cause', 'Fix'],
            ['"ModuleNotFoundError: No module named backend"', 'Running python backend/app.py directly', 'Run: python -m backend.app  (with PYTHONPATH set to project root)'],
            ['"Address already in use"', 'Port 5000 is occupied by another process', 'Run: netstat -ano | findstr :5000  → taskkill /F /PID <PID>'],
            ['"No module named flask"', 'Virtual environment not activated', 'Run: venv\\Scripts\\activate  then retry'],
        ], col_widths=[5 * cm, 4 * cm, CONTENT_W - 9 * cm]),
        sp(0.3),
    ]

    s.append(section('8.4  Email Not Sending'))
    s += [
        p('Work through this checklist in order:'),
        info_table([
            ['Check', 'How'],
            ['1. Is MAIL_PASSWORD set?', 'Open .env — check MAIL_PASSWORD is not the placeholder "your-gmail-app-password-here"'],
            ['2. Is it a Gmail App Password?', 'Must be a 16-char App Password, not your regular Gmail password — 2FA must be enabled'],
            ['3. Server restarted after .env change?', 'Kill the server and start it again — running process does not pick up .env changes'],
            ['4. Check email_dev.log', 'If dev mode is active, emails go to .claude/email_dev.log — open it to see what would have been sent'],
            ['5. Is Gmail account blocking access?', 'Check Gmail → Security → Recent security activity for blocked sign-in attempts'],
        ], col_widths=[5.5 * cm, CONTENT_W - 5.5 * cm]),
        sp(0.3),
    ]

    s.append(section('8.5  Frequently Asked Questions'))
    s += [
        subsection('Can a customer cancel their own booking?'),
        p('Yes. From /account/bookings.html, the customer can cancel any of their bookings. '
          'The status changes to "cancelled" and the booking remains visible in their history.'),

        subsection('What happens if a staff member forgets their temporary password?'),
        p('An Admin or Super Admin can reset it from the Staff page → Reset PW button. '
          'A new temporary password is generated and emailed to the staff member. It is also '
          'shown in the success toast.'),

        subsection('Can I change the markup or service fee?'),
        p('Yes — update DEFAULT_MARKUP_PERCENT and DEFAULT_SERVICE_FEE_USD in the .env file '
          'and restart the server. All new bookings will use the new rates. Existing bookings '
          'are not affected (prices are stored as a snapshot at booking time).'),

        subsection('Why do all searches return results even for unusual routes?'),
        p('The flight search engine is a mock system that generates realistic options for any '
          'valid airport pair. It is not connected to live airline inventory. This means any '
          'two airports in the 191-airport database will always return results.'),

        subsection('Can a Finance user see customer details?'),
        p('No. Finance role only has access to the Dashboard (bookings + revenue stats) and '
          'the Finance page. The Customers nav link is hidden, and the /api/admin/customers '
          'endpoint returns 403 for Finance tokens.'),

        subsection('How do I add a new staff member without them receiving an email?'),
        p('If email is not configured, the credentials email will silently fail but the account '
          'is still created. The temporary password is shown in the success modal on the Staff '
          'page immediately after creation — copy it and share it manually with the new staff member.'),

        subsection('Is the flight data real?'),
        p('No. All flight data — prices, times, availability, flight numbers, and status — is '
          'generated by a deterministic mock engine. The same search always returns the same results '
          'for a given route and date. This is intentional for the current version of the platform. '
          'Connecting to a live flight data API (e.g. Amadeus, Skyscanner) would replace the '
          'mock_flights.py service.'),

        subsection('What databases are supported?'),
        p('SQLite is used for local development (no setup required). PostgreSQL is used for '
          'production. The DATABASE_URL environment variable controls which is used. '
          'Any SQLAlchemy-compatible database works.'),

        subsection('How do I add a new airport?'),
        p('Open backend/services/mock_flights.py and add the airport to the AIRPORTS dictionary '
          'with its IATA code, name, city, country, region, latitude, and longitude. '
          'If the airport should have a carrier whitelist (e.g. a regional airport with limited '
          'airlines), add it to AIRPORT_CARRIERS with the list of eligible airline codes.'),
    ]

    # Final spacer
    s.append(sp(2))
    s.append(hr(GREEN, 1))
    s.append(p('End of Document — Airfinder Project Documentation v1.0', CAPTION))

    return s


# ──────────────────────────────────────────────────────────────────────────────
#  BUILD PDF
# ──────────────────────────────────────────────────────────────────────────────
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title='Airfinder Project Documentation',
        author='Airfinder Engineering Team',
        subject='Complete Project Documentation',
    )
    story = flatten(build_story())
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f'PDF generated: {output_path}')


if __name__ == '__main__':
    build_pdf('C:/Users/rigwe/Desktop/Airfinder_Documentation.pdf')
