from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Product


bp = Blueprint("products", __name__)


@bp.route("/")
def list_products():
    products = Product.query.order_by(Product.name.asc()).all()
    return render_template("products_list.html", products=products)


@bp.route("/new", methods=["GET", "POST"])
def new_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price = float(request.form.get("price", 0))
        stock_qty = int(request.form.get("stock_qty", 0))
        low_stock_threshold = int(request.form.get("low_stock_threshold", 10))
        next_url = request.form.get("next") or request.args.get("next")
        
        if not name or not category or price <= 0:
            flash("Please provide valid product details (name, category, and price > 0).")
        else:
            product = Product(
                name=name,
                category=category,
                price=price,
                stock_qty=stock_qty,
                low_stock_threshold=low_stock_threshold
            )
            db.session.add(product)
            db.session.commit()
            return redirect(next_url or url_for("products.list_products"))
    return render_template("product_form.html")


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form.get("name", "").strip()
        product.category = request.form.get("category", "").strip()
        product.price = float(request.form.get("price", 0))
        product.stock_qty = int(request.form.get("stock_qty", 0))
        product.low_stock_threshold = int(request.form.get("low_stock_threshold", 10))
        
        if not product.name or not product.category or product.price <= 0:
            flash("Please provide valid product details.")
        else:
            db.session.commit()
            next_url = request.form.get("next") or request.args.get("next")
            return redirect(next_url or url_for("products.list_products"))
    return render_template("product_form.html", product=product)


@bp.route("/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    next_url = request.form.get("next") or request.args.get("next")
    return redirect(next_url or url_for("products.list_products"))

