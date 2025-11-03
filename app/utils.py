import base64
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple

import requests
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash


def _ensure_fernet() -> Fernet:
    key = current_app.config.get("ENCRYPTION_KEY")
    if not key:
        # In production, enforce key presence
        raise RuntimeError("ENCRYPTION_KEY is not set. Provide a urlsafe base64 32-byte key.")
    # If a raw 32-byte is provided, base64-url encode it; otherwise assume already encoded
    try:
        # Validate by trying to construct
        return Fernet(key)
    except Exception:
        # Attempt encoding raw
        try:
            encoded = base64.urlsafe_b64encode(key.encode("utf-8"))
            return Fernet(encoded)
        except Exception as e:
            raise RuntimeError("Invalid ENCRYPTION_KEY; expected urlsafe base64 32-byte.") from e


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(hashed: str, password: str) -> bool:
    return check_password_hash(hashed, password)


def encrypt_text(value: Optional[str]) -> Optional[bytes]:
    if value is None:
        return None
    f = _ensure_fernet()
    return f.encrypt(value.encode("utf-8"))


def decrypt_text(value: Optional[bytes]) -> Optional[str]:
    if value is None:
        return None
    f = _ensure_fernet()
    try:
        return f.decrypt(value).decode("utf-8")
    except InvalidToken:
        return None


def encrypt_decimal(value: Decimal) -> bytes:
    return encrypt_text(str(value))  # type: ignore[return-value]


def decrypt_decimal(value: bytes) -> Decimal:
    s = decrypt_text(value)
    return Decimal(s or "0")


def encrypt_date(dt: datetime) -> bytes:
    return encrypt_text(dt.date().isoformat())  # type: ignore[return-value]


def decrypt_date(value: bytes) -> datetime:
    s = decrypt_text(value)
    return datetime.fromisoformat((s or "1970-01-01"))


def generate_otp() -> str:
    return f"{int.from_bytes(os.urandom(3), 'big') % 1000000:06d}"


def hash_otp(code: str) -> str:
    return generate_password_hash(code)


def verify_otp_hash(code_hash: str, code: str) -> bool:
    return check_password_hash(code_hash, code)


def send_email_otp_emailjs(to_email: str, company_name: str, otp_code: str) -> Tuple[bool, Optional[str]]:
    service_id = current_app.config.get("EMAILJS_SERVICE_ID")
    template_id = current_app.config.get("EMAILJS_TEMPLATE_ID")
    public_key = current_app.config.get("EMAILJS_PUBLIC_KEY")
    access_token = current_app.config.get("EMAILJS_ACCESS_TOKEN")

    # Basic fallback template if a custom template is not configured server-side
    html = f"""
    <div style='font-family:Arial,sans-serif;max-width:520px;margin:auto'>
      <h2>Login Verification Code</h2>
      <p>Hello {company_name},</p>
      <p>Your one-time password (OTP) is:</p>
      <div style='font-size:28px;font-weight:bold;letter-spacing:4px;margin:12px 0'>{otp_code}</div>
      <p>This code will expire in 10 minutes. If you did not request it, you can ignore this email.</p>
      <p>Thanks,<br/>Income–Expense Manager</p>
    </div>
    """

    # Provide multiple common params so typical EmailJS templates bind correctly
    payload = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": public_key,
        "accessToken": access_token,
        "template_params": {
            # common recipient fields
            "to_email": to_email,
            "to": to_email,
            "to_name": company_name,
            "user_email": to_email,
            "reply_to": to_email,
            "email": to_email,
            # message-specific
            "company_name": company_name,
            "otp_code": otp_code,
            "otp": otp_code,
            "code": otp_code,
            "message_html": html,
            "message": f"Your OTP is {otp_code}",
            "subject": "Your OTP Code",
        },
    }

    try:
        resp = requests.post("https://api.emailjs.com/api/v1.0/email/send", json=payload, timeout=20)
        if resp.status_code in (200, 202):
            return True, None
        # Attempt to extract message
        try:
            data = resp.json()
        except Exception:
            data = {"message": resp.text}
        return False, f"EmailJS error {resp.status_code}: {data.get('message') or data}"
    except Exception as e:
        return False, str(e)


