from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
from database import get_db


router = APIRouter()

templates = Jinja2Templates(directory="templates")


# =========================
# GET USER FROM COOKIE
# =========================
def get_user_from_cookie(request: Request, db: Session):

    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        user = auth.get_current_user(
            access_token=token,
            db=db
        )

        return user

    except Exception as e:
        print("AUTH ERROR:", e)
        return None


# =========================
# ROOT
# =========================
@router.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_user_from_cookie(request, db)

    if user:
        return RedirectResponse(
            url="/chat",
            status_code=302
        )

    return RedirectResponse(
        url="/login",
        status_code=302
    )


# =========================
# CHAT PAGE
# =========================
@router.get("/chat", response_class=HTMLResponse)
def chat_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_user_from_cookie(request, db)

    if not user:
        return RedirectResponse(
            url="/login",
            status_code=302
        )

    rooms = db.query(models.Room).all()

    return templates.TemplateResponse(
        request,
        "chat.html",
        {
            "user": user,
            "rooms": rooms
        }
    )


# =========================
# CURRENT USER API
# =========================
@router.get("/api/me")
def get_me(
    current_user=Depends(auth.get_current_user)
):

    return {
        "id": current_user.id,
        "username": current_user.username,
        "phone_number": current_user.phone_number,
        "avatar_color": current_user.avatar_color
    }


# =========================
# GET ROOMS
# =========================
@router.get(
    "/api/rooms",
    response_model=List[schemas.RoomOut]
)
def get_rooms(
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user)
):

    return db.query(models.Room).all()


# =========================
# CREATE ROOM
# =========================
@router.post(
    "/api/rooms",
    response_model=schemas.RoomOut
)
def create_room(
    room: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user)
):

    existing_room = (
        db.query(models.Room)
        .filter(models.Room.name == room.name)
        .first()
    )

    if existing_room:
        raise HTTPException(
            status_code=400,
            detail="Room name already exists"
        )

    new_room = models.Room(
        name=room.name,
        description=room.description
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)

    return new_room


# =========================
# GET MESSAGES
# =========================
@router.get(
    "/api/rooms/{room_id}/messages",
    response_model=List[schemas.MessageOut]
)
def get_messages(
    room_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user)
):

    messages = (
        db.query(models.Message)
        .filter(models.Message.room_id == room_id)
        .order_by(models.Message.timestamp.asc())
        .limit(100)
        .all()
    )

    return messages