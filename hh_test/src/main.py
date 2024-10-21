from fastapi import FastAPI, Depends
import fastapi_users
from contextlib import asynccontextmanager
from src.auth.base_config import auth_backend, fastapi_users,current_user
from src.auth.schemas import UserRead, UserCreate
from src.auth.models import User
from src.messages.websocket import router as router_ws
from fastapi_cache.backends.redis import RedisCacheBackend
from fastapi_cache import CacheRegistry
from redis import asyncio as aioredis
import aiofiles
import asyncio


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
# app.include_router(router_pages)
# app.include_router(router_coin)



# origins = [
#     "http://localhost",
#     "http://localhost:3000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"],
#     allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
#                    "Authorization"]
# )
