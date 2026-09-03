from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: str
    phone_number: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    phone_number: Optional[str] = None
    avatar_color: str

    class Config:
        from_attributes = True


class PhoneOTPRequest(BaseModel):
    phone_number: str


class PhoneOTPVerify(BaseModel):
    phone_number: str
    otp: str


class Token(BaseModel):
    access_token: str
    token_type: str


class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class RoomOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    content: str
    timestamp: datetime
    sender: UserOut
    room_id: int

    class Config:
        from_attributes = True