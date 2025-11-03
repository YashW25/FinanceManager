from datetime import datetime
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Transaction
from ..utils import decrypt_decimal, decrypt_text, encrypt_date, encrypt_decimal, encrypt_text


bp = Blueprint("transactions", __name__)


def _require_auth_redirect():
    if not session.get("company_id") or not session.get("otp_verified"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/", methods=["GET"])  # /txn/
def list_transactions():
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    txns = Transaction.query.filter_by(company_id=company_id).order_by(Transaction.created_at.desc()).all()
    items = []
    for t in txns:
        items.append(
            {
                "id": t.id,
                "date": decrypt_text(t.date_enc),
                "type": decrypt_text(t.type_enc),
                "category": decrypt_text(t.category_enc),
                "amount": decrypt_decimal(t.amount_enc),
                "notes": decrypt_text(t.notes_enc) or "",
            }
        )
    return render_template("transactions.html", items=items)


@bp.route("/add", methods=["POST"])  # /txn/add
def add_transaction():
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    t_type = request.form.get("type", "").strip()
    date_str = request.form.get("date", "").strip()
    category = request.form.get("category", "").strip()
    amount_str = request.form.get("amount", "0").strip()
    notes = request.form.get("notes")
    if not t_type or not date_str or not category or not amount_str:
        flash("All fields except notes are required.", "danger")
        return redirect(url_for("transactions.list_transactions"))
    try:
        amt = Decimal(amount_str)
        datetime.fromisoformat(date_str)
    except Exception:
        flash("Invalid date or amount.", "danger")
        return redirect(url_for("transactions.list_transactions"))
    txn = Transaction(
        company_id=company_id,
        date_enc=encrypt_text(date_str),
        type_enc=encrypt_text(t_type.lower()),
        category_enc=encrypt_text(category),
        amount_enc=encrypt_decimal(amt),
        notes_enc=encrypt_text(notes or ""),
    )
    db.session.add(txn)
    db.session.commit()
    flash("Transaction added.", "success")
    return redirect(url_for("transactions.list_transactions"))


@bp.route("/<int:txn_id>/delete", methods=["POST"])  # /txn/<id>/delete
def delete_transaction(txn_id: int):
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    txn = Transaction.query.filter_by(id=txn_id, company_id=company_id).first()
    if not txn:
        flash("Not found.", "warning")
        return redirect(url_for("transactions.list_transactions"))
    db.session.delete(txn)
    db.session.commit()
    flash("Deleted.", "info")
    return redirect(url_for("transactions.list_transactions"))


@bp.route("/<int:txn_id>/edit", methods=["POST"])  # /txn/<id>/edit
def edit_transaction(txn_id: int):
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    txn = Transaction.query.filter_by(id=txn_id, company_id=company_id).first()
    if not txn:
        flash("Not found.", "warning")
        return redirect(url_for("transactions.list_transactions"))
    t_type = request.form.get("type", "").strip()
    date_str = request.form.get("date", "").strip()
    category = request.form.get("category", "").strip()
    amount_str = request.form.get("amount", "0").strip()
    notes = request.form.get("notes")
    try:
        amt = Decimal(amount_str)
        datetime.fromisoformat(date_str)
    except Exception:
        flash("Invalid date or amount.", "danger")
        return redirect(url_for("transactions.list_transactions"))
    txn.date_enc = encrypt_text(date_str)
    txn.type_enc = encrypt_text(t_type.lower())
    txn.category_enc = encrypt_text(category)
    txn.amount_enc = encrypt_decimal(amt)
    txn.notes_enc = encrypt_text(notes or "")
    db.session.commit()
    flash("Updated.", "success")
    return redirect(url_for("transactions.list_transactions"))


