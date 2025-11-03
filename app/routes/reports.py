from datetime import date, timedelta
from flask import Blueprint, render_template
from sqlalchemy import func
from ..models import Sale, Product


bp = Blueprint("reports", __name__)


@bp.route("/")
def view_reports():
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    # Daily sales summary
    daily_sales = (
        Sale.query
        .filter(Sale.sale_date == today)
        .with_entities(func.sum(Sale.total_price).label('total'), func.count(Sale.id).label('count'))
        .first()
    )
    daily_total = float(daily_sales.total) if daily_sales.total else 0.0
    daily_count = daily_sales.count if daily_sales.count else 0
    
    # Weekly sales summary
    weekly_sales = (
        Sale.query
        .filter(Sale.sale_date >= week_ago)
        .with_entities(func.sum(Sale.total_price).label('total'), func.count(Sale.id).label('count'))
        .first()
    )
    weekly_total = float(weekly_sales.total) if weekly_sales.total else 0.0
    weekly_count = weekly_sales.count if weekly_sales.count else 0
    
    # Stock status
    all_products = Product.query.order_by(Product.name.asc()).all()
    low_stock_products = [p for p in all_products if p.is_low_stock]
    
    # Recent sales (last 10)
    recent_sales = Sale.query.order_by(Sale.sale_date.desc(), Sale.id.desc()).limit(10).all()
    
    # Create maps for template access
    products_map = {p.id: p for p in all_products}
    
    return render_template(
        "reports.html",
        daily_total=daily_total,
        daily_count=daily_count,
        weekly_total=weekly_total,
        weekly_count=weekly_count,
        low_stock_products=low_stock_products,
        all_products=all_products,
        recent_sales=recent_sales,
        products_map=products_map
    )
