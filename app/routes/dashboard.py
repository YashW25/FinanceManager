from collections import defaultdict
from decimal import Decimal

from flask import Blueprint, redirect, render_template, session, url_for

from ..models import Transaction
from ..utils import decrypt_decimal, decrypt_text


bp = Blueprint("dashboard", __name__)


def _require_auth_redirect():
    if not session.get("company_id") or not session.get("otp_verified"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/")
def index():
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    txns = Transaction.query.filter_by(company_id=company_id).order_by(Transaction.created_at.desc()).limit(10).all()

    total_income = Decimal("0")
    total_expense = Decimal("0")
    category_totals = defaultdict(Decimal)
    recent = []
    for t in txns:
        t_type = (decrypt_text(t.type_enc) or "").lower()
        amt = decrypt_decimal(t.amount_enc)
        category = decrypt_text(t.category_enc) or "Unknown"
        date_str = decrypt_text(t.date_enc) or ""
        if t_type == "income":
            total_income += amt
            category_totals[category] += amt
        elif t_type == "expense":
            total_expense += amt
            category_totals[category] -= amt
        recent.append(
            {
                "id": t.id,
                "date": date_str,
                "type": t_type,
                "category": category,
                "amount": amt,
            }
        )

    net_savings = total_income - total_expense

    # Prepare simple chart data
    labels = list(category_totals.keys())
    values = [float(category_totals[k]) for k in labels]

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        net_savings=net_savings,
        recent=recent,
        chart_labels=labels,
        chart_values=values,
    )


