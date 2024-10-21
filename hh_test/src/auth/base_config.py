from fastapi_users.authentication import (
    AuthenticationBackend, 
    CookieTransport, 
    JWTStrategy
)
from src.auth.manager import get_user_manager
from fastapi_users import FastAPIUsers
from src.config import SECRET_JWT
from src.auth.models import User

cookie_transport = CookieTransport(cookie_name='bonds', cookie_max_age=7200, cookie_secure=False, cookie_httponly=False, cookie_samesite="lax",cookie_domain='0.0.0.0')

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_JWT, lifetime_seconds=7200)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()