from src.auth.base_config import auth_backend, fastapi_users
from fastapi_cache.backends.redis import RedisCacheBackend
from src.messages.websocket import router as router_ws
from src.auth.schemas import UserRead, UserCreate
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from fastapi import FastAPI




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
