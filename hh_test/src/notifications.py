from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from src.config import NOTIFICATIONS_TGBOT_TOKEN
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from src.database import get_async_session
from sqlalchemy import select
from src.auth.models import User

API_TOKEN = NOTIFICATIONS_TGBOT_TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def get_user_id_by_username(username : str, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.username == username)
    result = (await session.execute(query)).scalars().all()[0]
    return result.tg_id
    
async def send_notification(username: str, sender : str, message: str, session: AsyncSession):
    # Получаем user ID по юзернейму из вашей базы данных или другого источника
    user_id = await get_user_id_by_username(username,session=session)  # Ваша функция для получения ID
    if user_id:
        await bot.send_message(user_id, f"From {sender} : {message}")
    else:
        print(f"User with username {username} not found.")

