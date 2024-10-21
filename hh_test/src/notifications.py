from src.config import NOTIFICATIONS_TGBOT_TOKEN

from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.auth.models import User

from aiogram import Bot, Dispatcher

from sqlalchemy import select
from fastapi import Depends



API_TOKEN = NOTIFICATIONS_TGBOT_TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def get_user_id_by_username(username : str, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.username == username)
    result = (await session.execute(query)).scalars().all()[0]
    return result.tg_id
    
async def send_notification(username: str, sender : str, message: str, session: AsyncSession):
    user_id = await get_user_id_by_username(username,session=session) 
    if user_id:
        await bot.send_message(user_id, f"From {sender} : {message}")
    else:
        print(f"User with username {username} not found.")

