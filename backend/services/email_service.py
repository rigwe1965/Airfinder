import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

_BRAND = '#407E3C'
_BRAND_DARK = '#2d5a2a'
_BG = '#f4f7f4'
_CARD_BG = '#ffffff'


def send_email(to_email: str, subject: str, html_body: str):
    app = current_app._get_current_object()
    mail_user = app.config.get('MAIL_USERNAME')
    mail_pass = app.config.get('MAIL_PASSWORD')
    mail_server = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = app.config.get('MAIL_PORT', 587)
    sender = app.config.get('MAIL_DEFAULT_SENDER', 'Airfinder <noreply@airfinder.com>')

    if not mail_user or not mail_pass or 'your-' in (mail_pass or ''):
        import pathlib
        log_path = pathlib.Path(__file__).parent.parent.parent / '.claude' / 'email_dev.log'
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n[EMAIL DEV MODE]\nTo: {to_email}\nSubject: {subject}\n---\n{html_body}\n===\n")
        return True

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def _e(value) -> str:
    """HTML-escape any user-influenced value before it goes into an email body."""
    return html.escape('' if value is None else str(value), quote=True)


def _base_url() -> str:
    return current_app.config.get('PUBLIC_BASE_URL', 'http://localhost:5000')


def _eur(amount):
    try:
        return f"€{float(amount):,.2f}"
    except (TypeError, ValueError):
        return "€0.00"


def _email_wrapper(content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ margin:0; padding:0; background:{_BG}; font-family:'Helvetica Neue',Arial,sans-serif; color:#1a1a1a; }}
  .wrap {{ max-width:600px; margin:32px auto; background:{_CARD_BG}; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08); }}
  .header {{ background:{_BRAND}; padding:28px 32px; }}
  .header h1 {{ margin:0; color:#fff; font-size:22px; font-weight:700; letter-spacing:-0.3px; }}
  .header p {{ margin:4px 0 0; color:rgba(255,255,255,0.8); font-size:13px; }}
  .body {{ padding:28px 32px; }}
  .ref-block {{ background:{_BG}; border-left:4px solid {_BRAND}; padding:14px 18px; border-radius:0 8px 8px 0; margin-bottom:24px; }}
  .ref-block .label {{ font-size:11px; text-transform:uppercase; letter-spacing:0.8px; color:#6b7280; margin-bottom:4px; }}
  .ref-block .ref {{ font-size:24px; font-weight:800; color:{_BRAND}; letter-spacing:1px; }}
  .section-title {{ font-size:12px; text-transform:uppercase; letter-spacing:0.8px; color:#6b7280; margin:0 0 10px; font-weight:600; }}
  .route-row {{ display:flex; align-items:center; gap:12px; margin-bottom:20px; }}
  .iata {{ font-size:32px; font-weight:800; color:#111; }}
  .arrow {{ color:{_BRAND}; font-size:20px; flex:1; text-align:center; }}
  .meta-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px; }}
  .meta-item .label {{ font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:0.6px; }}
  .meta-item .value {{ font-size:14px; font-weight:600; color:#111; margin-top:2px; }}
  .divider {{ border:none; border-top:1px solid #e5e7eb; margin:20px 0; }}
  .pax-list {{ list-style:none; padding:0; margin:0 0 20px; }}
  .pax-list li {{ padding:8px 12px; background:{_BG}; border-radius:6px; margin-bottom:6px; font-size:13px; font-weight:500; }}
  .price-table {{ width:100%; border-collapse:collapse; font-size:13px; margin-bottom:20px; }}
  .price-table td {{ padding:7px 0; color:#374151; }}
  .price-table td:last-child {{ text-align:right; font-weight:500; }}
  .price-table .total-row td {{ font-size:16px; font-weight:800; color:#111; border-top:2px solid #111; padding-top:10px; }}
  .cta {{ display:inline-block; background:{_BRAND}; color:#fff; text-decoration:none; padding:13px 28px; border-radius:8px; font-weight:700; font-size:14px; margin:4px 0 20px; }}
  .footer {{ background:{_BG}; padding:18px 32px; text-align:center; font-size:11px; color:#9ca3af; border-top:1px solid #e5e7eb; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>✈ Airfinder</h1>
    <p>Fly Smart, Pay Fair</p>
  </div>
  <div class="body">
    {content}
  </div>
  <div class="footer">
    &copy; 2026 Airfinder &nbsp;·&nbsp; All prices shown in EUR &nbsp;·&nbsp; This is an automated confirmation email.
  </div>
</div>
</body>
</html>"""


def _flight_leg_html(b: dict, show_ref: bool = True) -> str:
    pricing = b.get('pricing', {})
    passengers = b.get('passengers', [])
    cabin = (b.get('cabin_class') or 'economy').replace('_', ' ').title()
    flight_num = b.get('flight_number') or '—'
    baggage_fee = pricing.get('baggage_fee', 0)
    seat_fee = pricing.get('seat_fee', 0)

    ref_html = ''
    if show_ref:
        ref_html = f"""
        <div class="ref-block">
          <div class="label">Booking Reference</div>
          <div class="ref">{_e(b.get('reference', ''))}</div>
        </div>"""

    pax_items = ''
    for i, p in enumerate(passengers, 1):
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or f"Passenger {i}"
        pax_items += f'<li>👤 {_e(name)}</li>'

    price_rows = f"""
      <tr><td>Base fare ({len(passengers)} pax)</td><td>{_eur(pricing.get('base_fare', 0))}</td></tr>
      <tr><td>Service fee</td><td>{_eur(pricing.get('service_fee', 0))}</td></tr>"""
    if baggage_fee and float(baggage_fee) > 0:
        price_rows += f'<tr><td>Checked baggage</td><td>{_eur(baggage_fee)}</td></tr>'
    if seat_fee and float(seat_fee) > 0:
        price_rows += f'<tr><td>Seat selection</td><td>{_eur(seat_fee)}</td></tr>'

    return f"""
    {ref_html}
    <p class="section-title">Flight Details</p>
    <div class="route-row">
      <div class="iata">{_e(b.get('origin', ''))}</div>
      <div class="arrow">——✈——</div>
      <div class="iata">{_e(b.get('destination', ''))}</div>
    </div>
    <div class="meta-grid">
      <div class="meta-item"><div class="label">Date</div><div class="value">{_e(b.get('departure_date', '—'))}</div></div>
      <div class="meta-item"><div class="label">Airline</div><div class="value">{_e(b.get('airline', '—'))}</div></div>
      <div class="meta-item"><div class="label">Flight</div><div class="value">{_e(flight_num)}</div></div>
      <div class="meta-item"><div class="label">Cabin</div><div class="value">{_e(cabin)}</div></div>
    </div>
    <p class="section-title">Passengers</p>
    <ul class="pax-list">{pax_items}</ul>
    <p class="section-title">Price Breakdown</p>
    <table class="price-table">
      <tbody>
        {price_rows}
        <tr class="total-row"><td>Total</td><td>{_eur(pricing.get('total', 0))}</td></tr>
      </tbody>
    </table>"""


def send_welcome_email(to_email: str, first_name: str):
    subject = "Welcome to Airfinder"
    content = f"""
    <h2 style="margin-top:0;color:{_BRAND};">Welcome, {_e(first_name)}!</h2>
    <p>Your account is ready. Search for flights worldwide with full price transparency.</p>
    <a href="{_base_url()}" class="cta">Search Flights</a>
    """
    send_email(to_email, subject, _email_wrapper(content))


def send_password_reset_email(to_email: str, first_name: str, reset_link: str):
    subject = "Reset Your Airfinder Password"
    content = f"""
    <h2 style="margin-top:0;color:{_BRAND};">Password Reset</h2>
    <p>Hi {_e(first_name)}, we received a request to reset your password.</p>
    <a href="{_e(reset_link)}" class="cta">Reset Password</a>
    <p style="color:#6b7280;font-size:12px;margin-top:16px;">Link expires in 15 minutes. Didn't request this? Ignore this email.</p>
    """
    send_email(to_email, subject, _email_wrapper(content))


def send_staff_credentials_email(to_email: str, first_name: str, role: str, temp_password: str):
    subject = "Your Airfinder Staff Account"
    content = f"""
    <h2 style="margin-top:0;color:{_BRAND};">Welcome to the Team, {_e(first_name)}!</h2>
    <p>Your staff account has been created with role: <strong>{_e(role.replace('_', ' ').title())}</strong></p>
    <div style="background:{_BG};padding:16px;border-radius:8px;margin:16px 0;">
      <p style="margin:4px 0;"><strong>Email:</strong> {_e(to_email)}</p>
      <p style="margin:4px 0;"><strong>Temporary Password:</strong> <code style="background:#e0e0e0;padding:2px 6px;border-radius:4px;">{_e(temp_password)}</code></p>
    </div>
    <p style="color:#dc2626;font-weight:700;">You must change this password on first login.</p>
    <a href="{_base_url()}/admin/login.html" class="cta">Login to Staff Portal</a>
    """
    send_email(to_email, subject, _email_wrapper(content))


def send_booking_confirmation_email(to_email: str, first_name: str, booking: dict):
    ref = booking.get('reference', '')
    subject = f"Booking Confirmed — {ref}"
    total = _eur(booking.get('pricing', {}).get('total', 0))
    content = f"""
    <h2 style="margin-top:0;color:{_BRAND};">Booking Confirmed ✓</h2>
    <p>Hi {_e(first_name)}, your flight is booked. Safe travels!</p>
    {_flight_leg_html(booking, show_ref=True)}
    <hr class="divider">
    <a href="{_base_url()}/account/bookings.html" class="cta">Manage My Booking</a>
    """
    send_email(to_email, subject, _email_wrapper(content))


def send_multicity_confirmation_email(to_email: str, first_name: str, bookings: list, group_ref: str, combined_total: float):
    subject = f"Multi-City Booking Confirmed — {group_ref}"
    legs_html = ''
    for i, b in enumerate(bookings, 1):
        legs_html += f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px 20px;margin-bottom:16px;">
          <p style="margin:0 0 12px;font-size:13px;font-weight:700;color:{_BRAND};">LEG {i} &nbsp;·&nbsp; {_e(b.get('reference', ''))}</p>
          {_flight_leg_html(b, show_ref=False)}
        </div>"""

    content = f"""
    <h2 style="margin-top:0;color:{_BRAND};">Multi-City Booking Confirmed ✓</h2>
    <p>Hi {_e(first_name)}, your {len(bookings)}-leg itinerary is booked!</p>
    <div class="ref-block" style="margin-bottom:24px;">
      <div class="label">Group Reference</div>
      <div class="ref">{_e(group_ref)}</div>
    </div>
    <p class="section-title">Your Itinerary ({len(bookings)} flights)</p>
    {legs_html}
    <div style="background:{_BG};padding:14px 18px;border-radius:8px;text-align:right;margin-bottom:20px;">
      <span style="font-size:13px;color:#6b7280;">Combined Total &nbsp;</span>
      <span style="font-size:20px;font-weight:800;color:#111;">{_eur(combined_total)}</span>
    </div>
    <a href="{_base_url()}/account/bookings.html" class="cta">Manage My Bookings</a>
    """
    send_email(to_email, subject, _email_wrapper(content))
