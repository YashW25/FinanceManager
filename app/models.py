from datetime import date, datetime
from .extensions import db


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_qty = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=10)

    sales = db.relationship("Sale", backref="product", lazy=True)

    def __repr__(self):
        return f"<Product {self.name} ({self.category})>"

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.low_stock_threshold


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)

    sales = db.relationship("Sale", backref="customer", lazy=True)

    def __repr__(self):
        return f"<Customer {self.name}>"


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.Date, nullable=False, default=date.today)

    def __repr__(self):
        return f"<Sale {self.id} - Product {self.product_id} x{self.quantity}>"


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    transactions = db.relationship("Transaction", backref="company", lazy=True, cascade="all, delete-orphan")
    otps = db.relationship("OTP", backref="company", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.name}>"


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    # Store encrypted strings for PII/financial fields
    date_enc = db.Column(db.LargeBinary, nullable=False)
    type_enc = db.Column(db.LargeBinary, nullable=False)  # "income" or "expense"
    category_enc = db.Column(db.LargeBinary, nullable=False)
    amount_enc = db.Column(db.LargeBinary, nullable=False)
    notes_enc = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.id} company={self.company_id}>"


class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<OTP company={self.company_id} verified={self.verified}>"
