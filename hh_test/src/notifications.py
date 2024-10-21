from src.config import NOTIFICATIONS_TGBOT_TOKEN

from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.auth.models import User

from aiogram import Bot, Dispatcher

from src.logger import logger
from sqlalchemy import select
from fastapi import Depends


# инициализируем бота тг для уведомлений о непрочитанных сообщениях
API_TOKEN = NOTIFICATIONS_TGBOT_TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# получение tg_id юзера по username пользователя
async def get_user_id_by_username(username : str, session: AsyncSession = Depends(get_async_session)) -> int:
    query = select(User).where(User.username == username)
    result = (await session.execute(query)).scalars().all()[0]
    return result.tg_id

# отправка уведомления через тг
async def send_notification(username: str, sender : str, message: str, session: AsyncSession):
    user_id = await get_user_id_by_username(username,session=session) 
    if user_id:
        await bot.send_message(user_id, f"From {sender} : {message}")
    else:
        logger.info(f"User with username {username} not found.")

