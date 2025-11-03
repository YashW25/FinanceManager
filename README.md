# Income–Expense Manager (Flask + SQLAlchemy) — with OTP Login and Encryption

This project now includes a secure, multi-company Income–Expense Manager layered onto the existing Mini Store app. It provides:
- Authentication with Signup/Login per company
- EmailJS-based OTP verification (10-minute expiry)
- Encrypted storage of financial data (Fernet)
- Income/Expense CRUD, dashboard, reports, and CSV export

## Quick Start

### 1) Create virtualenv and install deps
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 2) Configure environment
Create `.env` in project root or set environment vars:
```bash
# Flask
SECRET_KEY=change-me

# Database (auto-detects):
# Use DATABASE_URL for MySQL/Cloud, or leave blank for SQLite at instance/ministore.sqlite3
# DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4

# Encryption (required): Fernet key (urlsafe base64 32 bytes). Generate with Python:
# >>> from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
ENCRYPTION_KEY=<paste-generated-key>

# EmailJS (provided)
EMAILJS_SERVICE_ID=service_s81iz4m
EMAILJS_TEMPLATE_ID=template_3k0qsip
EMAILJS_PUBLIC_KEY=s-y6ER6Y_clINy-Ws
EMAILJS_ACCESS_TOKEN=MNnxlKhQIyVk2Y7p0y0MN

# OTP expiry in minutes (optional)
OTP_EXPIRY_MINUTES=10
```

### 3) Initialize database
```bash
python run.py  # first run auto-creates tables
```

### 4) Run
```bash
python run.py
# Visit http://127.0.0.1:5000
```

## New Routes (Income–Expense Manager)
- `GET/POST /signup` — Create company account (sends welcome email)
- `GET/POST /login` — Enter email/password; OTP emailed
- `GET/POST /otp-verify` — Complete login using OTP
- `GET /` — Dashboard (requires session + OTP verified)
- `GET /txn/` — Transactions list and add form
- `POST /txn/add` — Create income/expense
- `POST /txn/<id>/edit` — Update transaction
- `POST /txn/<id>/delete` — Delete transaction
- `GET /reports` — Reports with filters (date range, category)
- `GET /reports/download` — CSV export of filtered data
- `GET /logout` — End session

## Security
- Passwords are hashed using `werkzeug.security`
- OTP stored hashed; 10-minute expiry
- All transaction fields (date, type, category, amount, notes) are encrypted at rest with Fernet
- Session-based access control; OTP must be verified to reach dashboard and beyond

## Deployment
- Works on Render/Railway/Flask-compatible hosts
- Set `DATABASE_URL`, `SECRET_KEY`, `ENCRYPTION_KEY`, and EmailJS vars in the platform dashboard
- SQLite will be used automatically if `DATABASE_URL` is not set

---
# Mini Store Management (Flask + SQLAlchemy)

A lightweight Store Management web application that demonstrates core DBMS concepts with a simple, clean UI. The app supports either MySQL or SQLite for quick setup.

## Features (MVP)
- **Product Management**: Add, edit, delete, and list products with name, category, price, and stock quantity.
- **Customer Management**: Add and view customers with contact information (phone, email).
- **Sales Management**: Record sales transactions (with date, product, quantity, total price) and auto-update stock.
- **Inventory Tracking**: Automatically mark products as low stock when below threshold; prevent negative stock.
- **Reports**: View daily/weekly sales summaries and stock status.

## Tech Stack
- **Backend**: Python 3, Flask, SQLAlchemy
- **Database**: MySQL or SQLite
- **Frontend**: Server-rendered HTML templates with minimal CSS

## Run Locally

### 1) Create a virtual environment and install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Choose your database
- **Easiest**: SQLite (default). No env vars needed.
- **MySQL**: set env vars or `DATABASE_URL`.

**Options:**
- Use `DATABASE_URL` directly, e.g. `export DATABASE_URL='mysql+pymysql://user:pass@127.0.0.1:3306/ministore?charset=utf8mb4'`
- Or set by parts (driver defaults to PyMySQL):
```bash
export DB_DIALECT=mysql
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=yourpass
export MYSQL_DB=ministore
```
- For SQLite custom path: `export SQLITE_PATH=/absolute/path/to/ministore.sqlite3`

### 3) Initialize the database
```bash
flask --app run.py init-db
flask --app run.py seed-demo   # optional demo data
```

### 4) Run the server
```bash
python run.py
```
Visit http://127.0.0.1:5000

## Database Schema

### Key Entities
- **Product**(id, name, category, price, stock_qty, low_stock_threshold)
- **Customer**(id, name, phone, email)
- **Sale**(id, product_id, customer_id, quantity, total_price, sale_date)

### Relationships
- Product 1→N Sale (a product can have many sales)
- Customer 1→N Sale (a customer can have many sales; customer is optional for walk-in sales)

## Key Features

### Inventory Management
- Products automatically track stock quantity
- Low stock warnings when quantity falls below threshold
- Stock is automatically decremented when sales are recorded
- Negative stock is prevented during sale recording

### Sales Processing
- Record sales with product, customer (optional), quantity, and date
- Total price is calculated automatically based on product price × quantity
- Stock is updated automatically after each sale

### Reports
- Daily sales summary (revenue and transaction count)
- Weekly sales summary (revenue and transaction count)
- Low stock products list
- Recent sales history

## Usage Examples

### Adding a Product
1. Navigate to Products → Add Product
2. Enter name, category, price, initial stock quantity, and low stock threshold
3. Save

### Recording a Sale
1. Navigate to Sales → Record Sale
2. Select a product (stock availability shown)
3. Optionally select a customer (or leave as walk-in)
4. Enter quantity and sale date
5. Total is calculated automatically
6. Stock is decremented automatically upon saving

### Viewing Reports
1. Navigate to Reports
2. View daily/weekly revenue summaries
3. Check low stock alerts
4. Review recent sales

## Project Structure
```
miniproject/
├── app/
│   ├── __init__.py          # App factory and configuration
│   ├── models.py            # SQLAlchemy models (Product, Customer, Sale)
│   ├── routes/
│   │   ├── main.py          # Dashboard route
│   │   ├── products.py      # Product CRUD routes
│   │   ├── customers.py     # Customer CRUD routes
│   │   ├── sales.py         # Sales recording routes
│   │   ├── reports.py       # Reports and analytics
│   │   ├── settings.py      # Database settings
│   │   └── sql_console.py   # SQL query console
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       └── style.css        # Minimal CSS styling
├── instance/
│   └── ministore.sqlite3    # SQLite database (default)
├── requirements.txt
├── run.py                   # Application entry point
└── README.md
```

## Minimal SDLC Artifacts (for your report)
- **SRS**: Problem scope, users (store manager, cashier), functional requirements (CRUD, inventory tracking, sales reporting), non-functional (simplicity, data integrity), constraints.
- **Design**: ER diagram for entities above; relational schema in 3NF; simple sequence for sale processing with stock update.
- **Implementation**: Framework choice (Flask), configuration for DB swapping, key modules (models, routes, templates).
- **Testing**: Manual cases (valid/invalid product, stock checks, sale recording with stock update, low stock alerts, negative stock prevention); optional Postman collection.
- **Conclusion**: What works, limits (single-store, no multi-branch complexity), and possible extensions (invoices, suppliers, purchase orders).

## Notes
- Default SQLite DB file path: `instance/ministore.sqlite3` (auto-created).
- If using MySQL, ensure the database exists and user has privileges.
- Keep scope small to avoid complexity: single store, simple stock tracking, no multi-location support.
- The system prevents negative stock during sales but allows manual stock adjustments through product editing.
