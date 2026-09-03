import secrets
import time
import re


# =========================
# OTP STORAGE
# =========================

# phone_number -> {
#     "code": "123456",
#     "expires_at": timestamp
# }
_otp_store = {}

# Phones that successfully verified their OTP
_verified_phones = set()

# OTP validity: 5 minutes
OTP_EXPIRY_SECONDS = 5 * 60


# =========================
# NORMALIZE PHONE
# =========================

def normalize_phone(phone: str) -> str:
    """
    Remove spaces, dashes and brackets.
    Keep an optional leading +.
    """

    phone = phone.strip()

    if phone.startswith("+"):
        return "+" + re.sub(r"\D", "", phone[1:])

    return re.sub(r"\D", "", phone)


# =========================
# VALIDATE PHONE
# =========================

def is_valid_phone(phone: str) -> bool:
    """
    Accept phone numbers containing 7-15 digits.
    """

    digits = phone.lstrip("+")

    return digits.isdigit() and 7 <= len(digits) <= 15


# =========================
# GENERATE OTP
# =========================

def generate_and_store_otp(phone: str) -> str:
    """
    Generate a 6-digit OTP and store it temporarily.
    """

    code = f"{secrets.randbelow(1_000_000):06d}"

    _otp_store[phone] = {
        "code": code,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS
    }

    # New OTP means previous verification is no longer valid
    _verified_phones.discard(phone)

    return code


# =========================
# SEND OTP
# =========================

def send_otp_sms(phone: str, code: str) -> None:
    """
    Demo SMS function.

    No real SMS provider is configured yet,
    so the OTP is printed to the terminal.
    """

    print("=" * 50)
    print(f"📱 DEMO OTP for {phone}: {code}")
    print("=" * 50)


# =========================
# VERIFY OTP
# =========================

def verify_otp(phone: str, code: str) -> bool:
    """
    Verify OTP and mark the phone as verified.
    """

    stored = _otp_store.get(phone)

    if not stored:
        return False

    # Check expiration
    if time.time() > stored["expires_at"]:
        _otp_store.pop(phone, None)
        return False

    # Compare OTP
    if str(code).strip() != stored["code"]:
        return False

    # OTP is correct
    _verified_phones.add(phone)

    # Remove used OTP
    _otp_store.pop(phone, None)

    return True


# =========================
# CHECK PHONE VERIFICATION
# =========================

def is_phone_verified(phone: str) -> bool:
    """
    Check whether the phone number has been successfully verified.
    """

    return phone in _verified_phones


# =========================
# CLEAR VERIFICATION
# =========================

def clear_verification(phone: str) -> None:
    """
    Remove verification status after registration.
    """

    _verified_phones.discard(phone)