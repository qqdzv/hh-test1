import datetime
import uuid

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr

from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    id: int
    email: str
    username : str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    
    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    username : str
    email: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    tg_id : int = None


