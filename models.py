

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
 
 
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(200), nullable=False)
    avatar_color = Column(String(20), default="#25D366")
    created_at = Column(DateTime, default=datetime.utcnow)
 
    messages = relationship("Message", back_populates="sender")
 
 
class Room(Base):
    __tablename__ = "rooms"
 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
 
    messages = relationship("Message", back_populates="room")
 
 
class Message(Base):
    __tablename__ = "messages"
 
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
 
    sender = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")
 
