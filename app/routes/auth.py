from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Company, OTP
from ..utils import (
    generate_otp,
    hash_otp,
    hash_password,
    send_email_otp_emailjs,
    verify_otp_hash,
    verify_password,
)


bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")
        if Company.query.filter((Company.email == email) | (Company.name == name)).first():
            flash("Company name or email already exists.", "danger")
            return render_template("signup.html")
        company = Company(name=name, email=email, password_hash=hash_password(password))
        db.session.add(company)
        db.session.commit()

        # Send welcome email using EmailJS
        _ok, _err = send_email_otp_emailjs(
            to_email=email,
            company_name=name,
            otp_code="WELCOME",
        )

        flash("Signup successful. Please login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("signup.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        company = Company.query.filter_by(email=email).first()
        if not company or not verify_password(company.password_hash, password):
            flash("Invalid credentials.", "danger")
            return render_template("login.html")

        # Generate and send OTP
        code = generate_otp()
        otp = OTP(
            company_id=company.id,
            code_hash=hash_otp(code),
            expires_at=datetime.utcnow() + timedelta(minutes=current_app.config.get("OTP_EXPIRY_MINUTES", 10)),
        )
        db.session.add(otp)
        db.session.commit()

        ok, err = send_email_otp_emailjs(to_email=company.email, company_name=company.name, otp_code=code)
        if not ok:
            flash(f"Failed to send OTP email: {err}", "danger")
            return render_template("login.html")

        session.clear()
        session["pending_company_id"] = company.id
        flash("OTP sent to your registered email.", "info")
        return redirect(url_for("auth.otp_verify"))
    return render_template("login.html")


@bp.route("/otp-verify", methods=["GET", "POST"])
def otp_verify():
    pending_id = session.get("pending_company_id")
    if not pending_id:
        flash("No login in progress.", "warning")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        raw = request.form.get("code", "")
        code = "".join(ch for ch in raw if ch.isdigit())
        if len(code) != 6:
            flash("Enter the 6-digit OTP.", "danger")
            return render_template("otp_verify.html")
        otp = (
            OTP.query.filter_by(company_id=pending_id, verified=False)
            .order_by(OTP.created_at.desc())
            .first()
        )
        if not otp:
            flash("OTP not found. Please login again.", "danger")
            return redirect(url_for("auth.login"))
        if datetime.utcnow() > otp.expires_at:
            flash("OTP expired. Please login again.", "danger")
            return redirect(url_for("auth.login"))
        if not verify_otp_hash(otp.code_hash, code):
            flash("Invalid OTP.", "danger")
            return render_template("otp_verify.html")

        otp.verified = True
        db.session.commit()

        session.clear()
        session["company_id"] = pending_id
        session["otp_verified"] = True
        flash("Logged in successfully.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("otp_verify.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


