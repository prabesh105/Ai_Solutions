# AI-Solutions Flask + MySQL Project

This is the updated AI-Solutions web application built with **HTML5, CSS3, JavaScript, Python Flask and MySQL through XAMPP**. The public UI follows the final wireframe structure and uses a blue/white modern AI-company visual style. The admin panel has been redesigned as a responsive SaaS-style dashboard with a collapsible left sidebar only.

## Main Features

### Public Website

- Responsive sticky navbar with hamburger menu on mobile
- Public navigation: Home, Solutions, Case Studies, Articles, Gallery, Events, Testimonials, Contact Us
- Modern homepage with hero CTAs, company introduction, services overview, why choose us, counters, case studies, testimonials and final call-to-action
- Solutions page with modern service cards, industry categories and request buttons
- Case Studies / Portfolio page with filterable project cards and before/after-style visual sections
- Articles / Blog page with search, category filter and pagination
- Photo Gallery page with responsive grid and lightbox preview
- Events page with pagination and registration button only for future events
- Testimonials page with stars, client/company details and responsive cards
- Contact Us form connected to MySQL with validation and success/error feedback
- Floating AI chatbot with:
  - modern responsive chat UI
  - typing indicator
  - timestamps
  - quick replies
  - fallback responses
  - chatbot inquiry capture
  - database storage for chat messages and leads

### Admin Panel

- Secure admin login with password hashing
- No public/top navigation inside admin area
- Collapsible left sidebar navigation:
  - Dashboard
  - Inquiries
  - Services
  - Blogs
  - Events
  - Gallery
  - Testimonials
  - Analytics
  - Event Registrations
  - Logout
- Dashboard cards for inquiries, chatbot leads, services, blogs and registrations
- Inquiry management with:
  - search
  - country filter
  - job title filter
  - date filter
  - company filter
  - status filter
  - sorting
  - status update
  - delete
  - admin reply/comment
  - professional email sending support
  - saved replies in database
- CSV and Excel export for all inquiries or filtered inquiries
- Analytics dashboard with charts and bars for:
  - monthly inquiries
  - country-based analytics
  - status breakdown
  - service popularity
- CRUD management for services, blogs/articles, events, gallery and testimonials

### Security and Quality

- Password hashing using Werkzeug
- CSRF protection for POST/JSON requests
- Secure session settings
- Input sanitization
- Parameterized SQL queries to reduce SQL injection risk
- Jinja escaping for XSS prevention
- Responsive and accessibility-aware semantic HTML
- Clean comments and beginner-friendly structure

## Folder Structure

```text
ai_solutions_flask_project/
│
├── app.py
├── config.py
├── database.sql
├── requirements.txt
├── README.md
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── uploads/
│       └── .gitkeep
│
└── templates/
    ├── base.html
    ├── index.html
    ├── services.html
    ├── case_studies.html
    ├── articles.html
    ├── article_detail.html
    ├── gallery.html
    ├── events.html
    ├── testimonials.html
    ├── contact.html
    ├── login.html
    ├── 404.html
    └── admin/
        ├── layout.html
        ├── dashboard.html
        ├── inquiries.html
        ├── analytics.html
        ├── registrations.html
        ├── services.html
        ├── service_form.html
        ├── articles.html
        ├── article_form.html
        ├── events.html
        ├── event_form.html
        ├── gallery.html
        ├── gallery_form.html
        ├── testimonials.html
        └── testimonial_form.html
```

## Requirements

- Python 3.10 or newer
- XAMPP with MySQL running
- phpMyAdmin
- A modern browser

## Installation Steps

### 1. Extract the project

Extract the ZIP file and open the project folder in VS Code or your preferred editor.

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start MySQL in XAMPP

1. Open XAMPP Control Panel.
2. Start **Apache** and **MySQL**.
3. Open phpMyAdmin.
4. Import the provided `database.sql` file.

The SQL file creates the database, tables, relationships and sample data automatically.

### 5. Check database settings

The default XAMPP settings are already configured in `config.py`:

```python
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "ai_solutions_db"
```

If your MySQL root user has a password, update `MYSQL_PASSWORD` in `config.py` or use environment variables.

### 6. Run the Flask server

```bash
python app.py
```

Open the website at:

```text
http://127.0.0.1:5000
```

## Admin Login

```text
URL: http://127.0.0.1:5000/login
Email: admin@ai-solutions.com
Password: admin123
```

After login, you will be redirected to the redesigned admin dashboard.

## Email / SMTP Configuration

Email is disabled by default so the project can run locally without SMTP errors. Contact form submissions, chatbot inquiries and admin replies are still saved to the database.

To enable emails, create a `.env` file in the project root:

```env
MAIL_ENABLED=true
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

For Gmail, use an App Password instead of your normal Gmail password.

Emails supported:

- Contact Us inquiry confirmation email
- Admin reply/comment email to the inquiry sender
- Professional HTML email template formatting

## Exporting Inquiries

From the admin inquiry page, use:

- **Export CSV** for `.csv`
- **Export Excel** for `.xlsx`

Exports respect the filters currently applied on the inquiry management page.

## Important Notes

- Import `database.sql` before running the site.
- Keep XAMPP MySQL running while using the website.
- Change `SECRET_KEY` before production deployment.
- Change the default admin password before production deployment.
- Email sending requires valid SMTP configuration.
- This is a local academic/project-ready Flask application, not a hosted deployment package.

## Common Problems

### Database error in browser

Check that:

1. XAMPP MySQL is running.
2. `database.sql` was imported.
3. The database name is `ai_solutions_db`.
4. Your MySQL username/password in `config.py` are correct.

### Emails are not sending

Check that:

1. `MAIL_ENABLED=true` is set.
2. SMTP credentials are valid.
3. Gmail App Password is used if you are using Gmail.
4. Internet access is available.

### Excel export not working

Run:

```bash
pip install openpyxl
```

or reinstall all requirements:

```bash
pip install -r requirements.txt
```
