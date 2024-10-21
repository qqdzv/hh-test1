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

templates = Jinja2Templates(directory="src/templates")

class UserSearchRequest(BaseModel):
    username: str

redis_fastapi = aioredis.from_url("redis://localhost")

@asynccontextmanager
async def lifespan(app: FastAPI):
    RedisCacheBackend(redis_fastapi)
    yield
    

app = FastAPI(
    title="Test",
    lifespan=lifespan
)

# app.mount("/static", StaticFiles(directory="static"), name="static")


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

