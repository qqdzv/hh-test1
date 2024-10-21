from src.auth.base_config import auth_backend, fastapi_users
from fastapi_cache.backends.redis import RedisCacheBackend
from src.messages.websocket import router as router_ws
from src.auth.schemas import UserRead, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Depends, Request
from src.auth.base_config import current_user
from starlette.responses import FileResponse
from fastapi.responses import HTMLResponse
from src.database import get_async_session
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from src.auth.models import User
from pydantic import BaseModel
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware

templates = Jinja2Templates(directory="src/templates")

class UserSearchRequest(BaseModel):
    username: str

redis_fastapi = aioredis.from_url("redis://redis:6379")

@asynccontextmanager
async def lifespan(app: FastAPI):
    RedisCacheBackend(redis_fastapi)
    yield
    

app = FastAPI(
    title="Test",
    lifespan=lifespan
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)

                          
app.include_router(router_ws)

@app.get("/login", response_class=HTMLResponse)
async def login():
    return FileResponse("src/templates/login.html")

@app.get("/home", response_class=HTMLResponse)
async def home(user = Depends(current_user)):
    return FileResponse("src/templates/home.html")

@app.get("/register", response_class=HTMLResponse)
async def register():
    return FileResponse("src/templates/register.html")

@app.post("/search_user")
async def search_user(
    data: UserSearchRequest, 
    session: AsyncSession = Depends(get_async_session),
    user = Depends(current_user)):

    if user.username == data.username:
        return {"exists": False}
    query = select(User).where(User.username == data.username)
    result = (await session.execute(query)).scalars().all()
    if len(result) == 0:
        return {"exists": False}
    else:
        return {"exists": True}

@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request, recipient: str, token: str):
    return templates.TemplateResponse("chat.html", {"request": request, "recipient": recipient, "token": token})



origins = [
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
    allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Authorization"],
)
