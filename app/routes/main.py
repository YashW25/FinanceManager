from datetime import date
from flask import Blueprint, render_template
from sqlalchemy import func
from ..models import Product, Customer, Sale


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    today = date.today()
    
    products = Product.query.order_by(Product.name.asc()).all()
    customers = Customer.query.order_by(Customer.name.asc()).all()
    recent_sales = Sale.query.order_by(Sale.sale_date.desc(), Sale.id.desc()).limit(20).all()
    
    # Calculate metrics
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    low_stock_count = sum(1 for p in products if p.is_low_stock)
    
    # Today's sales
    today_sales = (
        Sale.query
        .filter(Sale.sale_date == today)
        .with_entities(func.sum(Sale.total_price).label('total'))
        .first()
    )
    today_revenue = float(today_sales.total) if today_sales.total else 0.0
    
    metrics = {
        "products_count": total_products,
        "customers_count": total_customers,
        "low_stock_count": low_stock_count,
        "today_revenue": today_revenue,
    }
    
    products_map = {p.id: p for p in products}
    customers_map = {c.id: c for c in customers}

    return render_template(
        "dashboard.html",
        metrics=metrics,
        products=products,
        customers=customers,
        recent_sales=recent_sales,
        products_map=products_map,
        customers_map=customers_map,
    )
