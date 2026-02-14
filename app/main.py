from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import auth, health, items, reservations, wishlists
from app.core.config import settings
from app.core.websocket import socket_app

app = FastAPI(title="Wishlist API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(wishlists.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(reservations.router, prefix="/api")

app.mount("/", socket_app)
