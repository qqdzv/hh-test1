from src.notifications import send_notification
from sqlalchemy.ext.asyncio import AsyncSession
from src.messages.schemas import MessageAdd
from sqlalchemy import select,insert,update
from fastapi.responses import HTMLResponse
from src.database import get_async_session
from fastapi_users.jwt import decode_jwt
from src.messages.models import Message
from redis import asyncio as aioredis
from src.config import SECRET_JWT
from src.auth.models import User
from src.logger import logger
import json

from fastapi import (
    Depends, 
    APIRouter, 
    WebSocket, 
    WebSocketDisconnect
)

redis = aioredis.from_url("redis://localhost")

router = APIRouter()

active_connections = dict()

# раскодируем jwt токен и извлекаем user_id
async def get_user_id_from_jwt(token : str) -> int:
    encoded_jwt = decode_jwt(token, SECRET_JWT, algorithms="HS256",audience=["fastapi-users:auth"])
    return int(encoded_jwt['sub'])

# подключение к вебсокету для обмена сообщениями
@router.websocket("/ws/{receiver_username}")
async def websocket_endpoint(
    websocket: WebSocket,
    receiver_username: str,
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    await websocket.accept()
    user_id = (await get_user_id_from_jwt(token))
    
    query = select(User).where(User.id == user_id)
    result = (await session.execute(query)).scalars().all()[0]
    sender_username = result.username
    sender_id = result.id
    active_connections[sender_id] = websocket
    
    logger.info(f"Client {sender_username} connected {websocket.client}")

    try:
        
        query = select(User).where(User.username == receiver_username)
        result = (await session.execute(query)).scalars().all()
        if len(result) == 0:
            pass
        else:
            result = result[0]
            receiver_id = result.id
            await redis.set(str(sender_id)+':'+str(receiver_id), '1')
        
            await send_chat_history(websocket, session, sender_id, receiver_id)

        while True:
            data = await websocket.receive_text()
            message = (json.loads(data))['message']
            
            user_online = await redis.get(str(receiver_id)+':'+str(sender_id))
            if user_online is None:
                new_message = MessageAdd(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content=message,
                    is_read=False
                )
            else:
                new_message = MessageAdd(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content=message,
                    is_read=True
                )
            new_message = new_message.model_dump()
            stmt = insert(Message).values(**new_message)
            await session.execute(stmt)
            await session.commit()
            
            await websocket.send_text(f"[NOW] you : {message}")

            if user_online is not None:
                await send_message_to_recipient(receiver_id, sender_username, message)
            else:
                await send_notification(username=receiver_username,sender=sender_username,message=message,session=session)
                
    except WebSocketDisconnect:
        await redis.delete(str(sender_id)+':'+str(receiver_id))
        del active_connections[sender_id]
        logger.info(f"Client {sender_username} disconnected {websocket.client}")

async def send_chat_history(websocket: WebSocket, session: AsyncSession, sender_id: int, receiver_id: int):
    query = select(Message).where(
        (Message.sender_id == sender_id) & (Message.receiver_id == receiver_id) |
        (Message.sender_id == receiver_id) & (Message.receiver_id == sender_id)
    ).order_by(Message.created_at)
    
    messages = (await session.execute(query)).scalars().all()
    
    query = select(User).where(User.id == receiver_id)
    result = (await session.execute(query)).scalars().all()[0]
    receiver = result.username
    
    for message in messages:
        formatted_time = message.created_at.strftime("%d.%m %H:%M")  
        if message.sender_id == sender_id:
            if not message.is_read:
                await websocket.send_text(
                    f"[{formatted_time}] you : {message.content} ({receiver} not read yet)"
                )
            else:
                await websocket.send_text(
                    f"[{formatted_time}] you : {message.content}"
                )
        else:
            if not message.is_read:
                await websocket.send_text(
                    f"[{formatted_time}] {receiver}: {message.content} (new)"
                )
            else:
                await websocket.send_text(
                    f"[{formatted_time}] {receiver}: {message.content}"
                )
    await mark_messages_as_read(session=session,sender_id=receiver_id,receiver_id=sender_id)

# принятие сообщений собеседником если он онлайн
async def send_message_to_recipient(receiver_id: int, sender_username : str, message: str):
    if receiver_id in active_connections:
        recipient_websocket = active_connections[receiver_id]
        await recipient_websocket.send_text(f"[NOW] {sender_username} : {message}")
        
# смена статуса is_read после прочтения на True
async def mark_messages_as_read(session: AsyncSession, sender_id: int, receiver_id: int):
    stmt = (
        update(Message)
        .where(
            (Message.sender_id == sender_id) & (Message.receiver_id == receiver_id) & (Message.is_read == False)
        )
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.commit()
    