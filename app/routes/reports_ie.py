from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from io import StringIO

from flask import Blueprint, Response, redirect, render_template, request, session, url_for, make_response

from ..models import Transaction
from ..utils import decrypt_decimal, decrypt_text


bp = Blueprint("reports_ie", __name__)


def _require_auth_redirect():
    if not session.get("company_id") or not session.get("otp_verified"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/reports", methods=["GET"])  # /reports for income-expense manager
def reports_page():
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    start = request.args.get("start")
    end = request.args.get("end")
    category_filter = (request.args.get("category") or "").strip()

    txns = Transaction.query.filter_by(company_id=company_id).all()
    rows = []
    for t in txns:
        date_str = decrypt_text(t.date_enc) or ""
        t_type = decrypt_text(t.type_enc) or ""
        category = decrypt_text(t.category_enc) or ""
        amt = decrypt_decimal(t.amount_enc)
        if start and date_str < start:
            continue
        if end and date_str > end:
            continue
        if category_filter and category_filter.lower() not in category.lower():
            continue
        rows.append({"date": date_str, "type": t_type, "category": category, "amount": amt})

    # Summaries
    by_month = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})
    by_year = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})
    for r in rows:
        y, m, _ = r["date"].split("-")
        key_m = f"{y}-{m}"
        by_month[key_m][r["type"]] += r["amount"]
        by_year[y][r["type"]] += r["amount"]

    return render_template("reports.html", rows=rows, by_month=by_month, by_year=by_year, start=start, end=end, category=category_filter)


@bp.route("/reports/download", methods=["GET"])  # CSV download
def download_csv():
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    start = request.args.get("start")
    end = request.args.get("end")
    category_filter = (request.args.get("category") or "").strip()

    txns = Transaction.query.filter_by(company_id=company_id).all()
    sio = StringIO()
    sio.write("date,type,category,amount\n")
    for t in txns:
        date_str = decrypt_text(t.date_enc) or ""
        t_type = decrypt_text(t.type_enc) or ""
        category = decrypt_text(t.category_enc) or ""
        amt = decrypt_decimal(t.amount_enc)
        if start and date_str < start:
            continue
        if end and date_str > end:
            continue
        if category_filter and category_filter.lower() not in category.lower():
            continue
        sio.write(f"{date_str},{t_type},{category},{amt}\n")

    sio.seek(0)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return Response(
        sio.read(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=statement_{ts}.csv"},
    )


@bp.route("/reports/download-pdf", methods=["GET"])  # PDF download
def download_pdf():
    guard = _require_auth_redirect()
    if guard:
        return guard
    company_id = session["company_id"]
    start = request.args.get("start")
    end = request.args.get("end")

    txns = Transaction.query.filter_by(company_id=company_id).all()
    rows = []
    for t in txns:
        date_str = decrypt_text(t.date_enc) or ""
        t_type = decrypt_text(t.type_enc) or ""
        category = decrypt_text(t.category_enc) or ""
        amt = decrypt_decimal(t.amount_enc)
        if start and date_str < start:
            continue
        if end and date_str > end:
            continue
        rows.append({"date": date_str, "type": t_type, "category": category, "amount": amt, "notes": decrypt_text(t.notes_enc) or ""})

    # Render HTML and convert to PDF
    html = render_template("pdf_transactions.html", rows=rows, start=start, end=end)
    try:
        from xhtml2pdf import pisa  # type: ignore
    except Exception as e:
        return make_response(f"PDF generation unavailable: {e}", 500)

    from io import BytesIO
    pdf_io = BytesIO()
    result = pisa.CreatePDF(html, dest=pdf_io)
    if result.err:
        return make_response("Failed to generate PDF", 500)
    pdf_io.seek(0)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    resp = make_response(pdf_io.read())
    resp.headers["Content-Type"] = "application/pdf"
    resp.headers["Content-Disposition"] = f"attachment; filename=transactions_{ts}.pdf"
    return resp


