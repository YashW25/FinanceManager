import os


class Config:
    def __call__(self):
        return self

    def __init__(self):
        # Base defaults; DB URI finalized in create_app to use app.instance_path
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        # Encryption key for Fernet (urlsafe base64 32 bytes). Generate and set via env in production.
        self.ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
        # EmailJS credentials (use env in production)
        self.EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID", "service_s81iz4m")
        self.EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "template_3k0qsip")
        self.EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY", "s-y6ER6Y_clINy-Ws")
        self.EMAILJS_ACCESS_TOKEN = os.getenv("EMAILJS_ACCESS_TOKEN", "MNnxlKhQIyVk2Y7p0y0MN")
        # OTP expiry window in minutes
        self.OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
