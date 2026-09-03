from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import engine, SessionLocal
import models

from routers import auth_router, chat_router, ws_router

# ========================================
# CREATE DATABASE TABLES
# ========================================
models.Base.metadata.create_all(bind=engine)

# ========================================
# FASTAPI APP
# ========================================
app = FastAPI(
    title="WS Clone",
    version="1.0.0"
)

# ========================================
# STATIC FILES
# ========================================
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# ========================================
# ROUTERS
# ========================================
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(ws_router.router)


# ========================================
# CREATE DEFAULT ROOMS
# ========================================
@app.on_event("startup")
def create_default_rooms():

    db = SessionLocal()

    default_rooms = [
        {"name": "General", "description": "General chat for everyone 💬"},
        {"name": "Random", "description": "Anything goes! 🎲"},
        {"name": "Tech Talk", "description": "Discuss technology 💻"},
        {"name": "Music", "description": "Share what you're listening to 🎵"},
    ]

    for room_data in default_rooms:
        exists = (
            db.query(models.Room)
            .filter(models.Room.name == room_data["name"])
            .first()
        )
        if not exists:
            db.add(models.Room(**room_data))

    db.commit()
    db.close()
