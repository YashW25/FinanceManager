from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..extensions import db
from ..models import Customer


bp = Blueprint("customers", __name__)


@bp.route("/")
def list_customers():
    customers = Customer.query.order_by(Customer.name.asc()).all()
    return render_template("customers_list.html", customers=customers)


@bp.route("/new", methods=["GET", "POST"])
def new_customer():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        next_url = request.form.get("next") or request.args.get("next")
        if not name:
            flash("Please provide a customer name.")
        else:
            customer = Customer(name=name, phone=phone or None, email=email or None)
            db.session.add(customer)
            db.session.commit()
            return redirect(next_url or url_for("customers.list_customers"))
    return render_template("customer_form.html")


@bp.route("/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    next_url = request.form.get("next") or request.args.get("next")
    return redirect(next_url or url_for("customers.list_customers"))

