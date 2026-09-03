from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    JSONResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from sqlalchemy.orm import Session

import models
import auth
import schemas
import otp

from database import get_db

router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)

# =========================
# REGISTER PAGE
# =========================
@router.get(
    "/register",
    response_class=HTMLResponse
)
def register_page(
    request: Request
):

    return templates.TemplateResponse(
        request,
        "register.html",
        {}
    )

# =========================
# LOGIN PAGE
# =========================
@router.get(
    "/login",
    response_class=HTMLResponse
)
def login_page(
    request: Request
):

    return templates.TemplateResponse(
        request,
        "login.html",
        {}
    )

# =========================
# SEND OTP
# =========================
@router.post("/otp/send")
def send_otp(
    payload: schemas.PhoneOTPRequest,
    db: Session = Depends(get_db)
):

    phone = otp.normalize_phone(payload.phone_number)

    if not otp.is_valid_phone(phone):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid phone number (7-15 digits)"
        )

    existing = (
        db.query(models.User)
        .filter(models.User.phone_number == phone)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account already exists with this phone number"
        )

    code = otp.generate_and_store_otp(phone)
    otp.send_otp_sms(phone, code)

    return {
        "message": "OTP sent",
        # DEV-ONLY: real deployments should NOT echo the OTP back in the
        # response — this exists only because no real SMS provider is
        # wired in yet. Remove this field once one is.
        "dev_otp": code
    }

# =========================
# VERIFY OTP
# =========================
@router.post("/otp/verify")
def verify_otp_route(
    payload: schemas.PhoneOTPVerify
):

    phone = otp.normalize_phone(payload.phone_number)

    if not otp.verify_otp(phone, payload.otp):
        raise HTTPException(
            status_code=400,
            detail="Incorrect or expired OTP"
        )

    return {"message": "Phone verified"}

# =========================
# REGISTER USER
# =========================
@router.post("/register")
def register(

    payload: schemas.UserCreate,

    db: Session = Depends(get_db)

):

    phone = otp.normalize_phone(payload.phone_number)

    # PHONE MUST BE OTP-VERIFIED FIRST
    if not otp.is_phone_verified(phone):

        raise HTTPException(
            status_code=400,
            detail="Please verify your phone number first"
        )

    # CHECK EXISTING USER
    existing_user = (
        db.query(models.User)
        .filter(
            models.User.username ==
            payload.username
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # CHECK EXISTING PHONE (race-condition safety net)
    existing_phone = (
        db.query(models.User)
        .filter(models.User.phone_number == phone)
        .first()
    )

    if existing_phone:

        raise HTTPException(
            status_code=400,
            detail="An account already exists with this phone number"
        )

    # HASH PASSWORD
    hashed_password = auth.hash_password(
        payload.password
    )

    # CREATE USER
    new_user = models.User(
        username=payload.username,
        email=payload.email,
        phone_number=phone,
        hashed_password=hashed_password
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    otp.clear_verification(phone)

    print(
        f"✅ Registered user: {payload.username} ({phone})"
    )

    # JSON RESPONSE (frontend redirects itself)
    return {"message": "Account created"}

# =========================
# LOGIN USER
# =========================
@router.post("/login")
def login(

    payload: schemas.UserLogin,

    db: Session = Depends(get_db)

):

    print(
        f"🔐 Login attempt: {payload.username}"
    )

    # FIND USER
    user = (
        db.query(models.User)
        .filter(
            models.User.username ==
            payload.username
        )
        .first()
    )

    # INVALID USER
    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username"
        )

    # VERIFY PASSWORD
    valid_password = auth.verify_password(
        payload.password,
        user.hashed_password
    )

    # INVALID PASSWORD
    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    # CREATE JWT TOKEN
    token = auth.create_access_token(
        {
            "sub": user.username
        }
    )

    print(
        f"✅ Login success: {payload.username}"
    )

    # JSON RESPONSE (frontend redirects itself)
    response = JSONResponse(
        content={"message": "Login successful"}
    )

    # SAVE COOKIE
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=86400
    )

    return response

# =========================
# LOGOUT
# =========================
@router.post("/logout")
def logout():

    print("👋 User logged out")

    response = RedirectResponse(
        url="/login",
        status_code=302
    )

    response.delete_cookie(
        "access_token"
    )

    return response