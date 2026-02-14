import socketio

from app.core.config import settings

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.allowed_origins_list,
)
socket_app = socketio.ASGIApp(sio, socketio_path="/socket.io")


@sio.event
async def connect(sid, environ):
    pass


@sio.event
async def disconnect(sid):
    pass


@sio.on("join:wishlist")
async def join_wishlist(sid, data):
    slug = data.get("slug") if isinstance(data, dict) else data
    if slug:
        sio.enter_room(sid, f"wishlist:{slug}")


@sio.on("leave:wishlist")
async def leave_wishlist(sid, data):
    slug = data.get("slug") if isinstance(data, dict) else data
    if slug:
        sio.leave_room(sid, f"wishlist:{slug}")
