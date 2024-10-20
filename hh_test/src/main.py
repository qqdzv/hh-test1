from fastapi import FastAPI, Depends
import fastapi_users
from src.auth.base_config import auth_backend, fastapi_users,current_user
from src.auth.schemas import UserRead, UserCreate
from src.auth.models import User

app = FastAPI(
    title="Test",
    # lifespan=lifespan
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

                          
# app.include_router(router_operation)
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
