from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from decimal import Decimal
from ..extensions import db
from ..models import Product, Customer, Sale


bp = Blueprint("sales", __name__)


@bp.route("/")
def list_sales():
    sales = Sale.query.order_by(Sale.sale_date.desc(), Sale.id.desc()).all()
    products = {p.id: p for p in Product.query.all()}
    customers = {c.id: c for c in Customer.query.all()}
    return render_template("sales_list.html", sales=sales, products=products, customers=customers)


@bp.route("/new", methods=["GET", "POST"])
def new_sale():
    products = Product.query.order_by(Product.name.asc()).all()
    customers = Customer.query.order_by(Customer.name.asc()).all()
    
    if not products:
        flash("Create a product first.")
    
    if request.method == "POST":
        product_id = request.form.get("product_id")
        customer_id = request.form.get("customer_id") or None
        quantity = int(request.form.get("quantity", 1))
        date_str = request.form.get("sale_date")
        next_url = request.form.get("next") or request.args.get("next")
        
        if not product_id:
            flash("Select a product.")
        else:
            product = Product.query.get_or_404(int(product_id))
            
            if quantity <= 0:
                flash("Quantity must be greater than 0.")
            elif product.stock_qty < quantity:
                flash(f"Insufficient stock. Available: {product.stock_qty}")
            else:
                sale_date = date.fromisoformat(date_str) if date_str else date.today()
                total_price = Decimal(str(product.price)) * quantity
                
                sale = Sale(
                    product_id=int(product_id),
                    customer_id=int(customer_id) if customer_id else None,
                    quantity=quantity,
                    total_price=total_price,
                    sale_date=sale_date
                )
                db.session.add(sale)
                
                # Update product stock
                product.stock_qty -= quantity
                if product.stock_qty < 0:
                    product.stock_qty = 0
                
                db.session.commit()
                flash(f"Sale recorded successfully. Total: ${total_price:.2f}")
                return redirect(next_url or url_for("sales.list_sales"))
    
    return render_template("sale_form.html", products=products, customers=customers)

