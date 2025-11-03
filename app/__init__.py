import os
from flask import Flask
from .config import Config
from .extensions import db

# Optional .env support for easy local configuration
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):
        return None


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists for SQLite default
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Load env from .env if present
    load_dotenv()

    app.config.from_object(Config())

    # Default DB: SQLite under instance/ unless DATABASE_URL or MySQL env set
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        dialect = os.getenv("DB_DIALECT", "sqlite").lower()
        if dialect == "mysql":
            host = os.getenv("MYSQL_HOST", "127.0.0.1")
            port = os.getenv("MYSQL_PORT", "3306")
            user = os.getenv("MYSQL_USER", "root")
            password = os.getenv("MYSQL_PASSWORD", "")
            dbname = os.getenv("MYSQL_DB", "ministore")
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
            )
        else:
            sqlite_path = os.getenv("SQLITE_PATH") or os.path.join(app.instance_path, "ministore.sqlite3")
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"

    # Fallback to SQLite if the configured DB is unavailable
    try:
        from sqlalchemy import create_engine, text as _text
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if not uri.startswith("sqlite"):
            test_engine = create_engine(uri)
            with test_engine.connect() as conn:
                conn.execute(_text("select 1"))
    except Exception as e:
        sqlite_path = os.path.join(app.instance_path, "ministore.sqlite3")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
        print(f"[WARN] DB connection failed; falling back to SQLite at {sqlite_path}. Error: {e}")

    # Sensible defaults
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key"))

    # Init extensions
    db.init_app(app)

    # Ensure models are imported before creating tables
    from . import models  # noqa: F401

    # Create tables automatically on startup (idempotent)
    from flask import g, session, has_request_context
    from sqlalchemy import event
    with app.app_context():
        db.create_all()

        # Attach SQL listener within app context to access engine
        if not app.config.get("_SQL_LISTENER_SET") and os.getenv("DISABLE_SQL_LOG", "0") != "1":
            def _log_sql(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
                if has_request_context():
                    try:
                        g._sql_log.append((statement, parameters))
                    except Exception:
                        pass

            event.listen(db.engine, "before_cursor_execute", _log_sql)
            app.config["_SQL_LISTENER_SET"] = True

    @app.before_request
    def _sql_log_init():
        g._sql_log = []

    @app.after_request
    def _sql_log_store(response):
        def _fmt_value(v):
            from datetime import date, datetime
            if v is None:
                return "NULL"
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, (date, datetime)):
                return f"'{v.isoformat()}'"
            if isinstance(v, bool):
                return '1' if v else '0'
            # Escape single quotes for SQL display
            s = str(v).replace("'", "''")
            return f"'{s}'"

        def _render_sql(stmt: str, params):
            import re
            s = str(stmt)
            try:
                # Dict param styles: %(name)s or :name
                if isinstance(params, dict) and params:
                    # pyformat: %(name)s
                    def repl_pyformat(m):
                        key = m.group(1)
                        return _fmt_value(params.get(key))
                    s_py = re.sub(r"%\((\w+)\)s", repl_pyformat, s)
                    # named: :name
                    def repl_named(m):
                        key = m.group(1)
                        return _fmt_value(params.get(key))
                    s_named = re.sub(r":(\w+)", repl_named, s_py)
                    return s_named

                # Positional param styles: ? or %s
                if isinstance(params, (list, tuple)) and params:
                    vals = list(params)
                    # First try qmark '?'
                    if '?' in s:
                        out = []
                        it = iter(vals)
                        for ch in s:
                            if ch == '?':
                                try:
                                    out.append(_fmt_value(next(it)))
                                except StopIteration:
                                    out.append('?')
                            else:
                                out.append(ch)
                        return ''.join(out)
                    # Then try %s tokens
                    def repl_s(_m, it=iter(vals)):
                        try:
                            return _fmt_value(next(it))
                        except StopIteration:
                            return '%s'
                    s = re.sub(r"%s", repl_s, s)
                    return s
            except Exception:
                return s
            return s

        try:
            if hasattr(g, "_sql_log") and g._sql_log:
                # Store only the most recent executed statement
                stmt, params = g._sql_log[-1]
                session["last_sql"] = _render_sql(stmt, params)
        except Exception:
            pass
        return response

    @app.context_processor
    def inject_sql_log():
        return {"sql_recent": (session.get("last_sql") or "").strip()}

    # Register blueprints
    # Existing Mini Store blueprints (kept for backward compatibility)
    from .routes.main import bp as main_bp
    from .routes.customers import bp as customers_bp
    from .routes.sales import bp as sales_bp
    from .routes.products import bp as products_bp
    from .routes.reports import bp as reports_bp
    from .routes.settings import bp as settings_bp
    from .routes.sql_console import bp as sql_bp

    # Income–Expense Manager blueprints (register first to claim root routes)
    from .routes.auth import bp as auth_bp
    try:
        from .routes.dashboard import bp as dashboard_bp
    except Exception:
        dashboard_bp = None
    try:
        from .routes.transactions import bp as transactions_bp
    except Exception:
        transactions_bp = None
    try:
        from .routes.reports_ie import bp as reports_ie_bp
    except Exception:
        reports_ie_bp = None

    app.register_blueprint(auth_bp)
    if dashboard_bp:
        app.register_blueprint(dashboard_bp, url_prefix="/")
    if transactions_bp:
        app.register_blueprint(transactions_bp, url_prefix="/txn")
    if reports_ie_bp:
        app.register_blueprint(reports_ie_bp)

    # Existing Mini Store blueprints under /store to avoid conflicts
    app.register_blueprint(main_bp, url_prefix="/store")
    app.register_blueprint(customers_bp, url_prefix="/store/customers")
    app.register_blueprint(sales_bp, url_prefix="/store/sales")
    app.register_blueprint(products_bp, url_prefix="/store/products")
    app.register_blueprint(reports_bp, url_prefix="/store/reports")
    app.register_blueprint(settings_bp, url_prefix="/store/settings")
    app.register_blueprint(sql_bp, url_prefix="/store/sql")

    # CLI commands
    @app.cli.command("init-db")
    def init_db_cmd():
        from .models import Product, Customer, Sale  # noqa
        with app.app_context():
            db.create_all()
        print("Initialized the database.")

    @app.cli.command("seed-demo")
    def seed_demo_cmd():
        from datetime import date
        from decimal import Decimal
        from .models import Product, Customer, Sale
        with app.app_context():
            if not Product.query.first():
                products = [
                    Product(name="Laptop", category="Electronics", price=Decimal("999.99"), stock_qty=15, low_stock_threshold=5),
                    Product(name="Mouse", category="Electronics", price=Decimal("29.99"), stock_qty=50, low_stock_threshold=10),
                    Product(name="Keyboard", category="Electronics", price=Decimal("79.99"), stock_qty=30, low_stock_threshold=10),
                    Product(name="Notebook", category="Stationery", price=Decimal("5.99"), stock_qty=100, low_stock_threshold=20),
                    Product(name="Pen Set", category="Stationery", price=Decimal("12.99"), stock_qty=8, low_stock_threshold=10),
                    Product(name="Coffee Mug", category="Home", price=Decimal("15.99"), stock_qty=25, low_stock_threshold=5),
                ]
                db.session.add_all(products)
                db.session.commit()

            if not Customer.query.first():
                customers = [
                    Customer(name="John Doe", phone="555-0101", email="john@example.com"),
                    Customer(name="Jane Smith", phone="555-0102", email="jane@example.com"),
                    Customer(name="Bob Wilson", phone="555-0103"),
                    Customer(name="Alice Brown", email="alice@example.com"),
                ]
                db.session.add_all(customers)
                db.session.commit()

            if not Sale.query.first():
                # Create some sample sales
                products = Product.query.all()
                customers = Customer.query.all()
                if products and customers:
                    sales = [
                        Sale(product_id=products[0].id, customer_id=customers[0].id, quantity=1, total_price=products[0].price, sale_date=date.today()),
                        Sale(product_id=products[1].id, customer_id=customers[1].id, quantity=2, total_price=products[1].price * 2, sale_date=date.today()),
                        Sale(product_id=products[2].id, customer_id=customers[0].id, quantity=1, total_price=products[2].price, sale_date=date.today()),
                    ]
                    # Update stock for seeded sales
                    for sale in sales:
                        product = Product.query.get(sale.product_id)
                        if product:
                            product.stock_qty -= sale.quantity
                    db.session.add_all(sales)
                    db.session.commit()
        print("Seeded demo data.")

    return app
