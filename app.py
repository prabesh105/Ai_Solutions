from datetime import date, datetime
from functools import wraps
import csv
import html
import io
import re
import secrets
from dotenv import load_dotenv
load_dotenv()

import mysql.connector
from mysql.connector import Error
from flask import Flask, Response, abort, flash, jsonify, redirect, render_template, request, session, url_for
from markupsafe import Markup
from werkzeug.security import check_password_hash

try:
    from flask_mail import Mail, Message
except Exception:
    Mail = None
    Message = None

try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

from config import Config


app = Flask(__name__)
app.config.from_object(Config)
print("MAIL_ENABLED =", app.config.get("MAIL_ENABLED"))
print("MAIL_SERVER =", app.config.get("MAIL_SERVER"))
print("MAIL_USERNAME =", app.config.get("MAIL_USERNAME"))
mail = Mail(app) if Mail else None

ALLOWED_INQUIRY_STATUS = ["New", "Contacted", "In Progress", "Closed"]
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def csrf_field():
    return Markup(f'<input type="hidden" name="csrf_token" value="{csrf_token()}">')


@app.before_request
def csrf_protect():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        if not sent or sent != session.get("_csrf_token"):
            abort(400, description="Invalid or missing CSRF token.")


def clean_text(value, max_length=5000):
    value = (value or "").strip()
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return value[:max_length]


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email or ""))


def get_connection():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        port=app.config["MYSQL_PORT"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DATABASE"],
    )


def db_query(query, params=None, fetch="all", commit=False):
    params = params or ()
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        if commit:
            connection.commit()
            return cursor.lastrowid
        if fetch == "one":
            return cursor.fetchone()
        if fetch == "none":
            return None
        return cursor.fetchall()
    except Error as error:
        print(f"Database error: {error}")
        if request.endpoint not in {"chatbot_message", "chatbot_inquiry"}:
            flash("Database error. Please check XAMPP MySQL and import database.sql.", "danger")
        return [] if fetch == "all" else None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def slugify(text):
    text = clean_text(text, 180).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please login to access the admin area.", "warning")
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_global_values():
    return {"current_year": date.today().year, "today": date.today(), "csrf_token": csrf_token, "csrf_field": csrf_field}


def send_html_email(to_email, subject, html_body, text_body=None):
    if not app.config.get("MAIL_ENABLED"):
        return "Email disabled - saved in database only"
    if not mail or not Message:
        return "Email library is not installed"
    try:
        message = Message(subject=subject, recipients=[to_email])
        message.html = html_body
        message.body = text_body or re.sub(r"<[^>]+>", "", html_body)
        mail.send(message)
        return "Sent"
    except Exception as exc:
        print(f"Email error: {exc}")
        return f"Email failed: {exc}"


def email_template(title, greeting, body):
    return f"""
    <div style="font-family:Arial,sans-serif;background:#f5f8ff;padding:24px">
      <div style="max-width:680px;margin:auto;background:#fff;border-radius:18px;overflow:hidden;border:1px solid #dbe7ff">
        <div style="background:linear-gradient(135deg,#0f6dfd,#173fc9);padding:28px;color:white">
          <h1 style="margin:0;font-size:24px">{html.escape(title)}</h1>
          <p style="margin:8px 0 0">AI-Solutions Customer Support</p>
        </div>
        <div style="padding:28px;color:#172033;line-height:1.7">
          <p><strong>{html.escape(greeting)}</strong></p>
          {body}
          <p style="margin-top:26px">Regards,<br><strong>AI-Solutions Team</strong></p>
        </div>
      </div>
    </div>
    """


def send_inquiry_confirmation(inquiry):
    body = f"""
    <p>Thank you for contacting AI-Solutions. We have received your inquiry and our team will review your requirements shortly.</p>
    <p><strong>Company:</strong> {html.escape(inquiry.get('company') or 'Not provided')}<br>
       <strong>Service interest:</strong> {html.escape(inquiry.get('service_interest') or 'General inquiry')}</p>
    <p>We normally respond as soon as possible with a suitable recommendation or next step.</p>
    """
    return send_html_email(inquiry["email"], "We received your AI-Solutions inquiry", email_template("Inquiry Received", f"Hello {inquiry['name']},", body))


# Public pages
@app.route("/")
def index():
    services = db_query("SELECT * FROM services WHERE is_active = 1 ORDER BY display_order ASC, id ASC LIMIT 3")
    articles = db_query("SELECT * FROM articles WHERE is_active = 1 ORDER BY is_featured DESC, published_at DESC LIMIT 3")
    events = db_query("SELECT * FROM events WHERE is_active = 1 AND event_date >= %s ORDER BY event_date ASC LIMIT 3", (date.today(),))
    testimonials = db_query("SELECT * FROM testimonials WHERE is_active = 1 ORDER BY id DESC LIMIT 6")
    case_studies = db_query("SELECT * FROM case_studies WHERE is_active = 1 ORDER BY is_featured DESC, id DESC LIMIT 3")
    stats = {"projects": 42, "clients": 28, "support": "24/7", "satisfaction": "98%"}
    return render_template("index.html", services=services, articles=articles, events=events, testimonials=testimonials, case_studies=case_studies, stats=stats)


@app.route("/services")
def services():
    services_list = db_query("SELECT * FROM services WHERE is_active = 1 ORDER BY display_order ASC, id ASC")
    industries = db_query("SELECT DISTINCT industry FROM services WHERE is_active = 1 AND industry <> '' ORDER BY industry ASC")
    return render_template("services.html", services=services_list, industries=industries)


@app.route("/case-studies")
def case_studies():
    selected_category = clean_text(request.args.get("category"), 80)
    query = "SELECT * FROM case_studies WHERE is_active = 1"
    params = []
    if selected_category:
        query += " AND category = %s"
        params.append(selected_category)
    query += " ORDER BY is_featured DESC, id DESC"
    cases = db_query(query, tuple(params))
    categories = db_query("SELECT DISTINCT category FROM case_studies WHERE is_active = 1 ORDER BY category")
    return render_template("case_studies.html", cases=cases, categories=categories, selected_category=selected_category)


@app.route("/articles")
def articles():
    search = clean_text(request.args.get("search"), 120)
    category = clean_text(request.args.get("category"), 80)
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = 6
    offset = (page - 1) * per_page
    where = "WHERE is_active = 1"
    params = []
    if search:
        where += " AND (title LIKE %s OR summary LIKE %s OR content LIKE %s)"
        keyword = f"%{search}%"
        params.extend([keyword, keyword, keyword])
    if category:
        where += " AND category = %s"
        params.append(category)
    total_row = db_query(f"SELECT COUNT(*) AS total FROM articles {where}", tuple(params), fetch="one")
    total = total_row["total"] if total_row else 0
    total_pages = max((total + per_page - 1) // per_page, 1)
    articles_list = db_query(f"SELECT * FROM articles {where} ORDER BY is_featured DESC, published_at DESC, id DESC LIMIT %s OFFSET %s", tuple(params + [per_page, offset]))
    categories = db_query("SELECT DISTINCT category FROM articles WHERE is_active = 1 ORDER BY category ASC")
    return render_template("articles.html", articles=articles_list, categories=categories, search=search, selected_category=category, page=page, total_pages=total_pages)


@app.route("/articles/<slug>")
def article_detail(slug):
    article = db_query("SELECT * FROM articles WHERE slug = %s AND is_active = 1", (slug,), fetch="one")
    if not article:
        abort(404)
    return render_template("article_detail.html", article=article)


@app.route("/gallery")
def gallery():
    category = clean_text(request.args.get("category"), 80)
    query = "SELECT * FROM gallery_items WHERE is_active = 1"
    params = []
    if category:
        query += " AND category = %s"
        params.append(category)
    query += " ORDER BY id DESC"
    items = db_query(query, tuple(params))
    categories = db_query("SELECT DISTINCT category FROM gallery_items WHERE is_active = 1 ORDER BY category")
    events_preview = db_query("SELECT * FROM events WHERE is_active = 1 ORDER BY event_date ASC LIMIT 3")
    return render_template("gallery.html", items=items, categories=categories, selected_category=category, events=events_preview)


@app.route("/events")
def events():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = 5
    offset = (page - 1) * per_page
    total_row = db_query("SELECT COUNT(*) AS total FROM events WHERE is_active = 1", fetch="one")
    total = total_row["total"] if total_row else 0
    total_pages = max((total + per_page - 1) // per_page, 1)
    event_list = db_query("SELECT * FROM events WHERE is_active = 1 ORDER BY event_date ASC, event_time ASC LIMIT %s OFFSET %s", (per_page, offset))
    return render_template("events.html", events=event_list, page=page, total_pages=total_pages)


@app.route("/events/register/<int:event_id>", methods=["POST"])
def register_event(event_id):
    event = db_query("SELECT * FROM events WHERE id = %s AND is_active = 1", (event_id,), fetch="one")
    if not event:
        abort(404)
    if event["event_date"] <= date.today():
        flash("Registration is closed for this event.", "warning")
        return redirect(url_for("events"))
    name = clean_text(request.form.get("name"), 120)
    email = clean_text(request.form.get("email"), 160).lower()
    phone = clean_text(request.form.get("phone"), 40)
    if not name or not is_valid_email(email):
        flash("Please enter a valid name and email.", "danger")
        return redirect(url_for("events"))
    db_query("INSERT INTO event_registrations (event_id, name, email, phone) VALUES (%s, %s, %s, %s)", (event_id, name, email, phone), commit=True)
    flash("Registration submitted successfully.", "success")
    return redirect(url_for("events"))


@app.route("/testimonials")
def testimonials():
    items = db_query("SELECT * FROM testimonials WHERE is_active = 1 ORDER BY rating DESC, id DESC")
    return render_template("testimonials.html", testimonials=items)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    requested_service = clean_text(request.args.get("service"), 150)
    services_list = db_query("SELECT title FROM services WHERE is_active = 1 ORDER BY display_order ASC, id ASC")
    if request.method == "POST":
        form = {
            "name": clean_text(request.form.get("name"), 120),
            "email": clean_text(request.form.get("email"), 160).lower(),
            "phone": clean_text(request.form.get("phone"), 40),
            "company": clean_text(request.form.get("company"), 150),
            "country": clean_text(request.form.get("country"), 100),
            "job_title": clean_text(request.form.get("job_title"), 120),
            "job_details": clean_text(request.form.get("job_details"), 1800),
            "service_interest": clean_text(request.form.get("service_interest") or requested_service, 150),
        }
        errors = [field.replace("_", " ").title() for field in ["name", "email", "phone", "company", "country", "job_title", "job_details"] if not form[field]]
        if not is_valid_email(form["email"]):
            errors.append("Valid Email")
        if errors:
            flash("Please complete the following correctly: " + ", ".join(sorted(set(errors))) + ".", "danger")
            return render_template("contact.html", requested_service=requested_service, services=services_list, form=form)
        inquiry_id = db_query("""
            INSERT INTO contact_inquiries
            (name, email, phone, company, country, job_title, job_details, message, service_interest, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'New')
        """, (form["name"], form["email"], form["phone"], form["company"], form["country"], form["job_title"], form["job_details"], form["job_details"], form["service_interest"]), commit=True)
        form["id"] = inquiry_id
        email_status = send_inquiry_confirmation(form)
        db_query("UPDATE contact_inquiries SET confirmation_email_status=%s WHERE id=%s", (email_status, inquiry_id), commit=True)
        flash("Thank you. Your inquiry has been submitted successfully.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html", requested_service=requested_service, services=services_list, form={})


# Chatbot API
def chatbot_reply(user_message):
    message = user_message.lower()
    if any(word in message for word in ["service", "solution", "offer", "provide"]):
        return "We provide AI virtual assistants, AI prototyping, software engineering, automation dashboards and analytics systems."
    if any(word in message for word in ["price", "cost", "budget", "quote"]):
        return "Pricing depends on scope, timeline and integrations. Please share your company, email and requirement for a detailed quotation."
    if any(word in message for word in ["contact", "email", "phone", "support"]):
        return "You can use Contact Us, or I can save your inquiry here if you provide your name, email and requirement."
    if any(word in message for word in ["admin", "dashboard", "analytics"]):
        return "Our admin dashboard supports inquiry management, status tracking, analytics, replies and CSV/Excel exports."
    if any(word in message for word in ["hello", "hi", "hey"]):
        return "Hello! I can guide you to services, case studies, articles or help collect your inquiry details."
    return "I can help with services, pricing, contact information, case studies and inquiry submission. What type of AI or web solution do you need?"


@app.route("/api/chatbot/message", methods=["POST"])
def chatbot_message():
    payload = request.get_json(silent=True) or {}
    user_message = clean_text(payload.get("message"), 1000)
    if not user_message:
        return jsonify({"reply": "Please type a message so I can help.", "timestamp": datetime.now().strftime("%I:%M %p")})
    visitor_token = session.get("chatbot_visitor") or secrets.token_hex(12)
    session["chatbot_visitor"] = visitor_token
    reply = chatbot_reply(user_message)
    db_query("INSERT INTO chatbot_messages (visitor_token, user_message, bot_reply, page_url) VALUES (%s, %s, %s, %s)", (visitor_token, user_message, reply, clean_text(payload.get("page_url"), 500)), commit=True)
    return jsonify({"reply": reply, "timestamp": datetime.now().strftime("%I:%M %p")})


@app.route("/api/chatbot/inquiry", methods=["POST"])
def chatbot_inquiry():
    payload = request.get_json(silent=True) or {}
    form = {
        "name": clean_text(payload.get("name"), 120),
        "email": clean_text(payload.get("email"), 160).lower(),
        "phone": clean_text(payload.get("phone"), 40),
        "company": clean_text(payload.get("company"), 150),
        "message": clean_text(payload.get("message"), 1800),
        "service_interest": clean_text(payload.get("service_interest"), 150),
    }
    if not form["name"] or not is_valid_email(form["email"]) or not form["message"]:
        return jsonify({"ok": False, "message": "Please provide your name, valid email and requirement."}), 400
    visitor_token = session.get("chatbot_visitor") or secrets.token_hex(12)
    session["chatbot_visitor"] = visitor_token
    chatbot_id = db_query("INSERT INTO chatbot_inquiries (visitor_token, name, email, phone, company, service_interest, message) VALUES (%s, %s, %s, %s, %s, %s, %s)", (visitor_token, form["name"], form["email"], form["phone"], form["company"], form["service_interest"], form["message"]), commit=True)
    contact_id = db_query("""
        INSERT INTO contact_inquiries
        (name, email, phone, company, country, job_title, job_details, message, service_interest, status, source)
        VALUES (%s, %s, %s, %s, '', 'Chatbot Lead', %s, %s, %s, 'New', 'Chatbot')
    """, (form["name"], form["email"], form["phone"], form["company"], form["message"], form["message"], form["service_interest"]), commit=True)
    send_inquiry_confirmation({**form, "id": contact_id, "job_title": "Chatbot Lead"})
    return jsonify({"ok": True, "message": "Your inquiry has been saved. Our team will contact you soon.", "chatbot_id": chatbot_id})


# Authentication
@app.route("/login", methods=["GET", "POST"])
def login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        email = clean_text(request.form.get("email"), 160).lower()
        password = request.form.get("password", "")
        admin = db_query("SELECT * FROM admins WHERE email = %s AND is_active = 1", (email,), fetch="one")
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session.permanent = True
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]
            session["admin_email"] = admin["email"]
            csrf_token()
            flash("Welcome back, admin.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# Admin
def admin_counts():
    return {
        "inquiries": db_query("SELECT COUNT(*) AS total FROM contact_inquiries", fetch="one"),
        "chatbot": db_query("SELECT COUNT(*) AS total FROM chatbot_inquiries", fetch="one"),
        "services": db_query("SELECT COUNT(*) AS total FROM services", fetch="one"),
        "articles": db_query("SELECT COUNT(*) AS total FROM articles", fetch="one"),
        "events": db_query("SELECT COUNT(*) AS total FROM events", fetch="one"),
        "registrations": db_query("SELECT COUNT(*) AS total FROM event_registrations", fetch="one"),
    }


def analytics_payload():
    monthly = db_query("SELECT DATE_FORMAT(created_at, '%Y-%m') AS label, COUNT(*) AS total FROM contact_inquiries GROUP BY DATE_FORMAT(created_at, '%Y-%m') ORDER BY label ASC LIMIT 12")
    country = db_query("SELECT COALESCE(NULLIF(country,''), 'Unknown') AS label, COUNT(*) AS total FROM contact_inquiries GROUP BY label ORDER BY total DESC LIMIT 8")
    status = db_query("SELECT status AS label, COUNT(*) AS total FROM contact_inquiries GROUP BY status")
    services = db_query("SELECT COALESCE(NULLIF(service_interest,''), 'General') AS label, COUNT(*) AS total FROM contact_inquiries GROUP BY label ORDER BY total DESC LIMIT 8")
    return {"monthly": monthly, "country": country, "status": status, "services": services}


@app.route("/admin")
@login_required
def admin_dashboard():
    latest_inquiries = db_query("SELECT * FROM contact_inquiries ORDER BY created_at DESC LIMIT 5")
    return render_template("admin/dashboard.html", counts=admin_counts(), latest_inquiries=latest_inquiries, analytics=analytics_payload())


def inquiry_query_from_request():
    search = clean_text(request.args.get("search"), 120)
    status = clean_text(request.args.get("status"), 50)
    country = clean_text(request.args.get("country"), 100)
    job_title = clean_text(request.args.get("job_title"), 120)
    company = clean_text(request.args.get("company"), 150)
    date_from = clean_text(request.args.get("date_from"), 20)
    date_to = clean_text(request.args.get("date_to"), 20)
    sort = clean_text(request.args.get("sort"), 40) or "newest"
    query = "SELECT * FROM contact_inquiries WHERE 1=1"
    params = []
    if search:
        keyword = f"%{search}%"
        query += " AND (name LIKE %s OR email LIKE %s OR company LIKE %s OR job_title LIKE %s OR message LIKE %s OR service_interest LIKE %s)"
        params.extend([keyword] * 6)
    if status:
        query += " AND status = %s"
        params.append(status)
    if country:
        query += " AND country = %s"
        params.append(country)
    if job_title:
        query += " AND job_title LIKE %s"
        params.append(f"%{job_title}%")
    if company:
        query += " AND company LIKE %s"
        params.append(f"%{company}%")
    if date_from:
        query += " AND DATE(created_at) >= %s"
        params.append(date_from)
    if date_to:
        query += " AND DATE(created_at) <= %s"
        params.append(date_to)
    sort_map = {"newest": "created_at DESC", "oldest": "created_at ASC", "name": "name ASC", "country": "country ASC", "company": "company ASC", "status": "status ASC"}
    query += f" ORDER BY {sort_map.get(sort, 'created_at DESC')}"
    filters = {"search": search, "status": status, "country": country, "job_title": job_title, "company": company, "date_from": date_from, "date_to": date_to, "sort": sort}
    return query, tuple(params), filters


@app.route("/admin/inquiries")
@login_required
def admin_inquiries():
    query, params, filters = inquiry_query_from_request()
    inquiries = db_query(query, params)
    countries = db_query("SELECT DISTINCT country FROM contact_inquiries WHERE country <> '' ORDER BY country")
    return render_template("admin/inquiries.html", inquiries=inquiries, filters=filters, countries=countries, statuses=ALLOWED_INQUIRY_STATUS)


@app.route("/admin/inquiries/<int:inquiry_id>/status", methods=["POST"])
@login_required
def update_inquiry_status(inquiry_id):
    status = clean_text(request.form.get("status"), 40)
    if status not in ALLOWED_INQUIRY_STATUS:
        status = "New"
    db_query("UPDATE contact_inquiries SET status = %s WHERE id = %s", (status, inquiry_id), commit=True)
    flash("Inquiry status updated.", "success")
    return redirect(request.referrer or url_for("admin_inquiries"))


@app.route("/admin/inquiries/<int:inquiry_id>/reply", methods=["POST"])
@login_required
def reply_inquiry(inquiry_id):
    inquiry = db_query("SELECT * FROM contact_inquiries WHERE id = %s", (inquiry_id,), fetch="one")
    if not inquiry:
        abort(404)
    subject = clean_text(request.form.get("subject"), 200) or "Reply from AI-Solutions"
    body = clean_text(request.form.get("reply_body"), 5000)
    if not body:
        flash("Reply message cannot be empty.", "danger")
        return redirect(url_for("admin_inquiries"))
    body_html = "".join(f"<p>{html.escape(p)}</p>" for p in body.split("\n") if p.strip())
    email_status = send_html_email(inquiry["email"], subject, email_template(subject, f"Hello {inquiry['name']},", body_html))
    db_query("INSERT INTO inquiry_replies (inquiry_id, admin_id, subject, reply_body, email_status) VALUES (%s, %s, %s, %s, %s)", (inquiry_id, session.get("admin_id"), subject, body, email_status), commit=True)
    db_query("UPDATE contact_inquiries SET status='Contacted', admin_comment=%s WHERE id=%s", (body, inquiry_id), commit=True)
    flash(f"Reply saved. Email status: {email_status}", "success")
    return redirect(url_for("admin_inquiries"))


@app.route("/admin/inquiries/<int:inquiry_id>/delete", methods=["POST"])
@login_required
def delete_inquiry(inquiry_id):
    db_query("DELETE FROM contact_inquiries WHERE id = %s", (inquiry_id,), commit=True)
    flash("Inquiry deleted.", "info")
    return redirect(url_for("admin_inquiries"))


@app.route("/admin/inquiries/export/<fmt>")
@login_required
def export_inquiries(fmt):
    query, params, filters = inquiry_query_from_request()
    rows = db_query(query, params)
    columns = ["id", "name", "email", "phone", "company", "country", "job_title", "service_interest", "status", "source", "created_at", "job_details"]
    filename = f"ai_solutions_inquiries_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}.csv"})
    if fmt == "excel":
        if Workbook is None:
            flash("openpyxl is not installed. Please run pip install -r requirements.txt.", "danger")
            return redirect(url_for("admin_inquiries"))
        wb = Workbook()
        ws = wb.active
        ws.title = "Inquiries"
        ws.append(columns)
        for row in rows:
            ws.append([row.get(col) for col in columns])
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return Response(output.read(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"})
    abort(404)


@app.route("/admin/analytics")
@login_required
def admin_analytics():
    return render_template("admin/analytics.html", counts=admin_counts(), analytics=analytics_payload())


@app.route("/admin/registrations")
@login_required
def admin_registrations():
    registrations = db_query("SELECT r.*, e.title AS event_title, e.event_date FROM event_registrations r JOIN events e ON r.event_id = e.id ORDER BY r.created_at DESC")
    return render_template("admin/registrations.html", registrations=registrations)


# Generic CRUD helpers implemented as individual routes
@app.route("/admin/services")
@login_required
def admin_services():
    items = db_query("SELECT * FROM services ORDER BY display_order ASC, id ASC")
    return render_template("admin/services.html", services=items)


@app.route("/admin/services/new", methods=["GET", "POST"])
@login_required
def create_service():
    if request.method == "POST":
        title = clean_text(request.form.get("title"), 150)
        slug = clean_text(request.form.get("slug"), 170) or slugify(title)
        db_query("INSERT INTO services (title, slug, short_description, description, icon, industry, display_order, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (title, slug, clean_text(request.form.get("short_description"), 255), clean_text(request.form.get("description"), 5000), clean_text(request.form.get("icon"), 40) or "🤖", clean_text(request.form.get("industry"), 100), request.form.get("display_order", 0, type=int), 1 if request.form.get("is_active") else 0), commit=True)
        flash("Service created successfully.", "success")
        return redirect(url_for("admin_services"))
    return render_template("admin/service_form.html", service=None)


@app.route("/admin/services/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_service(item_id):
    service = db_query("SELECT * FROM services WHERE id = %s", (item_id,), fetch="one")
    if not service:
        abort(404)
    if request.method == "POST":
        title = clean_text(request.form.get("title"), 150)
        slug = clean_text(request.form.get("slug"), 170) or slugify(title)
        db_query("UPDATE services SET title=%s, slug=%s, short_description=%s, description=%s, icon=%s, industry=%s, display_order=%s, is_active=%s WHERE id=%s", (title, slug, clean_text(request.form.get("short_description"), 255), clean_text(request.form.get("description"), 5000), clean_text(request.form.get("icon"), 40) or "🤖", clean_text(request.form.get("industry"), 100), request.form.get("display_order", 0, type=int), 1 if request.form.get("is_active") else 0, item_id), commit=True)
        flash("Service updated successfully.", "success")
        return redirect(url_for("admin_services"))
    return render_template("admin/service_form.html", service=service)


@app.route("/admin/services/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_service(item_id):
    db_query("DELETE FROM services WHERE id = %s", (item_id,), commit=True)
    flash("Service deleted.", "info")
    return redirect(url_for("admin_services"))


@app.route("/admin/articles")
@login_required
def admin_articles():
    items = db_query("SELECT * FROM articles ORDER BY published_at DESC, id DESC")
    return render_template("admin/articles.html", articles=items)


@app.route("/admin/articles/new", methods=["GET", "POST"])
@login_required
def create_article():
    if request.method == "POST":
        title = clean_text(request.form.get("title"), 200)
        slug = clean_text(request.form.get("slug"), 220) or slugify(title)
        db_query("INSERT INTO articles (title, slug, category, author, summary, content, image_url, published_at, is_featured, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (title, slug, clean_text(request.form.get("category"), 100), clean_text(request.form.get("author"), 100) or "Admin", clean_text(request.form.get("summary"), 900), clean_text(request.form.get("content"), 15000), clean_text(request.form.get("image_url"), 500), request.form.get("published_at"), 1 if request.form.get("is_featured") else 0, 1 if request.form.get("is_active") else 0), commit=True)
        flash("Article created successfully.", "success")
        return redirect(url_for("admin_articles"))
    return render_template("admin/article_form.html", article=None)


@app.route("/admin/articles/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_article(item_id):
    article = db_query("SELECT * FROM articles WHERE id = %s", (item_id,), fetch="one")
    if not article:
        abort(404)
    if request.method == "POST":
        title = clean_text(request.form.get("title"), 200)
        slug = clean_text(request.form.get("slug"), 220) or slugify(title)
        db_query("UPDATE articles SET title=%s, slug=%s, category=%s, author=%s, summary=%s, content=%s, image_url=%s, published_at=%s, is_featured=%s, is_active=%s WHERE id=%s", (title, slug, clean_text(request.form.get("category"), 100), clean_text(request.form.get("author"), 100) or "Admin", clean_text(request.form.get("summary"), 900), clean_text(request.form.get("content"), 15000), clean_text(request.form.get("image_url"), 500), request.form.get("published_at"), 1 if request.form.get("is_featured") else 0, 1 if request.form.get("is_active") else 0, item_id), commit=True)
        flash("Article updated successfully.", "success")
        return redirect(url_for("admin_articles"))
    return render_template("admin/article_form.html", article=article)


@app.route("/admin/articles/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_article(item_id):
    db_query("DELETE FROM articles WHERE id = %s", (item_id,), commit=True)
    flash("Article deleted.", "info")
    return redirect(url_for("admin_articles"))


@app.route("/admin/events")
@login_required
def admin_events():
    items = db_query("SELECT * FROM events ORDER BY event_date ASC, event_time ASC")
    return render_template("admin/events.html", events=items)


@app.route("/admin/events/new", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        db_query("INSERT INTO events (title, event_date, event_time, location, short_description, description, image_url, category, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (clean_text(request.form.get("title"), 200), request.form.get("event_date"), request.form.get("event_time"), clean_text(request.form.get("location"), 200), clean_text(request.form.get("short_description"), 255), clean_text(request.form.get("description"), 5000), clean_text(request.form.get("image_url"), 500), clean_text(request.form.get("category"), 100), 1 if request.form.get("is_active") else 0), commit=True)
        flash("Event created successfully.", "success")
        return redirect(url_for("admin_events"))
    return render_template("admin/event_form.html", event=None)


@app.route("/admin/events/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(item_id):
    event = db_query("SELECT * FROM events WHERE id = %s", (item_id,), fetch="one")
    if not event:
        abort(404)
    if request.method == "POST":
        db_query("UPDATE events SET title=%s, event_date=%s, event_time=%s, location=%s, short_description=%s, description=%s, image_url=%s, category=%s, is_active=%s WHERE id=%s", (clean_text(request.form.get("title"), 200), request.form.get("event_date"), request.form.get("event_time"), clean_text(request.form.get("location"), 200), clean_text(request.form.get("short_description"), 255), clean_text(request.form.get("description"), 5000), clean_text(request.form.get("image_url"), 500), clean_text(request.form.get("category"), 100), 1 if request.form.get("is_active") else 0, item_id), commit=True)
        flash("Event updated successfully.", "success")
        return redirect(url_for("admin_events"))
    return render_template("admin/event_form.html", event=event)


@app.route("/admin/events/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_event(item_id):
    db_query("DELETE FROM events WHERE id = %s", (item_id,), commit=True)
    flash("Event deleted.", "info")
    return redirect(url_for("admin_events"))


@app.route("/admin/gallery")
@login_required
def admin_gallery():
    items = db_query("SELECT * FROM gallery_items ORDER BY id DESC")
    return render_template("admin/gallery.html", items=items)


@app.route("/admin/gallery/new", methods=["GET", "POST"])
@login_required
def create_gallery_item():
    if request.method == "POST":
        db_query("INSERT INTO gallery_items (title, category, image_url, description, gradient_class, is_active) VALUES (%s, %s, %s, %s, %s, %s)", (clean_text(request.form.get("title"), 150), clean_text(request.form.get("category"), 100), clean_text(request.form.get("image_url"), 500), clean_text(request.form.get("description"), 1000), clean_text(request.form.get("gradient_class"), 60) or "gradient-blue", 1 if request.form.get("is_active") else 0), commit=True)
        flash("Gallery item created successfully.", "success")
        return redirect(url_for("admin_gallery"))
    return render_template("admin/gallery_form.html", item=None)


@app.route("/admin/gallery/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_gallery_item(item_id):
    item = db_query("SELECT * FROM gallery_items WHERE id = %s", (item_id,), fetch="one")
    if not item:
        abort(404)
    if request.method == "POST":
        db_query("UPDATE gallery_items SET title=%s, category=%s, image_url=%s, description=%s, gradient_class=%s, is_active=%s WHERE id=%s", (clean_text(request.form.get("title"), 150), clean_text(request.form.get("category"), 100), clean_text(request.form.get("image_url"), 500), clean_text(request.form.get("description"), 1000), clean_text(request.form.get("gradient_class"), 60) or "gradient-blue", 1 if request.form.get("is_active") else 0, item_id), commit=True)
        flash("Gallery item updated successfully.", "success")
        return redirect(url_for("admin_gallery"))
    return render_template("admin/gallery_form.html", item=item)


@app.route("/admin/gallery/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_gallery_item(item_id):
    db_query("DELETE FROM gallery_items WHERE id = %s", (item_id,), commit=True)
    flash("Gallery item deleted.", "info")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/testimonials")
@login_required
def admin_testimonials():
    items = db_query("SELECT * FROM testimonials ORDER BY id DESC")
    return render_template("admin/testimonials.html", testimonials=items)


@app.route("/admin/testimonials/new", methods=["GET", "POST"])
@login_required
def create_testimonial():
    if request.method == "POST":
        db_query("INSERT INTO testimonials (name, role, company, rating, quote, image_url, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)", (clean_text(request.form.get("name"), 120), clean_text(request.form.get("role"), 120), clean_text(request.form.get("company"), 120), request.form.get("rating", 5, type=int), clean_text(request.form.get("quote"), 1000), clean_text(request.form.get("image_url"), 500), 1 if request.form.get("is_active") else 0), commit=True)
        flash("Testimonial created successfully.", "success")
        return redirect(url_for("admin_testimonials"))
    return render_template("admin/testimonial_form.html", testimonial=None)


@app.route("/admin/testimonials/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_testimonial(item_id):
    testimonial = db_query("SELECT * FROM testimonials WHERE id = %s", (item_id,), fetch="one")
    if not testimonial:
        abort(404)
    if request.method == "POST":
        db_query("UPDATE testimonials SET name=%s, role=%s, company=%s, rating=%s, quote=%s, image_url=%s, is_active=%s WHERE id=%s", (clean_text(request.form.get("name"), 120), clean_text(request.form.get("role"), 120), clean_text(request.form.get("company"), 120), request.form.get("rating", 5, type=int), clean_text(request.form.get("quote"), 1000), clean_text(request.form.get("image_url"), 500), 1 if request.form.get("is_active") else 0, item_id), commit=True)
        flash("Testimonial updated successfully.", "success")
        return redirect(url_for("admin_testimonials"))
    return render_template("admin/testimonial_form.html", testimonial=testimonial)


@app.route("/admin/testimonials/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_testimonial(item_id):
    db_query("DELETE FROM testimonials WHERE id = %s", (item_id,), commit=True)
    flash("Testimonial deleted.", "info")
    return redirect(url_for("admin_testimonials"))


@app.errorhandler(400)
def bad_request(error):
    return render_template("404.html", message=getattr(error, "description", "Bad request.")), 400


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", message="The page you requested was not found."), 404


if __name__ == "__main__":
    app.run(debug=True)
