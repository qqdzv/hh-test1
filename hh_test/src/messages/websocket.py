from typing import Annotated
from fastapi import (
    Cookie, 
    Depends, 
    APIRouter, 
    WebSocket, 
    WebSocketDisconnect, 
    status
)
from src.auth.models import User
from sqlalchemy import select,insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import WebSocketException
from fastapi.responses import HTMLResponse
from src.config import SECRET_JWT
from fastapi_users.jwt import SecretType, decode_jwt, generate_jwt
from src.database import get_async_session
from src.messages.schemas import MessageAdd
from src.messages.models import Message
from src.notifications import send_notification
import json
from redis import asyncio as aioredis


redis = aioredis.from_url("redis://localhost")

router = APIRouter()

# Секретный ключ для подписи JWT (в реальных приложениях храните его в переменных окружения)

html = '''
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket JWT</title>
</head>
<body>
    <h1>WebSocket JWT Chat</h1>
    <form action="" onsubmit="sendMessage(event)">
        <label for="recipient">Recipient:</label>
        <input type="text" id="recipient" autocomplete="off" placeholder="Enter recipient's username"/>
        <hr>
        <label for="messageText">Message:</label>
        <input type="text" id="messageText" autocomplete="off" placeholder="Type your message"/>
        <button onclick="connect(event)">Connect</button>
        <button type="submit">Send</button>
    </form>
    <ul id='messages'></ul>
    <script>
    var ws = null;

    // Функция для получения значения куки по имени
    function getCookie(name) {
        console.log("Searching for cookie...");
        let cookieArr = document.cookie.split(";");
        for (let i = 0; i < cookieArr.length; i++) {
            let cookiePair = cookieArr[i].trim().split("=");
            if (name === cookiePair[0].trim()) {
                console.log("Cookie found: ", cookiePair[1]);
                return decodeURIComponent(cookiePair[1]);
            }
        }
        console.log("Cookie not found.");
        return null;
    }

    // Функция для подключения к WebSocket
    function connect(event) {
        console.log("Attempting to connect...");

        const token = getCookie('bonds'); // Убедитесь, что имя токена верное
        if (!token) {
            alert('Token is missing! Please log in first.');
            return;
        }

        const recipient = document.getElementById("recipient").value.trim(); // Получаем получателя
        if (!recipient) {
            alert('Please enter a recipient.');
            return;
        }

        ws = new WebSocket(`ws://localhost:8000/ws/${recipient}?token=${token}`);
        ws.onmessage = function(event) {
            var messages = document.getElementById('messages');
            var message = document.createElement('li');
            var content = document.createTextNode(event.data);
            message.appendChild(content);
            messages.appendChild(message);
        };
        event.preventDefault();
    }


    // Функция для отправки сообщения
    function sendMessage(event) {
        var recipient = document.getElementById("recipient").value.trim(); // Получаем получателя
        var input = document.getElementById("messageText").value; // Получаем текст сообщения
        if (!recipient || !input) {
            alert('Please enter both recipient and message.');
            return;
        }

        // Формируем сообщение
        var messageData = JSON.stringify({ recipient: recipient, message: input });
        ws.send(messageData); // Отправляем сообщение на сервер
        document.getElementById("messageText").value = ''; // Очищаем поле ввода сообщения
        event.preventDefault();
    }
    </script>
</body>
</html>


'''

active_connections = dict()

@router.get("/")
async def get():
    return HTMLResponse(html)

async def get_user_id_from_jwt(token : str):
    encoded_jwt = decode_jwt(token, SECRET_JWT, algorithms="HS256",audience=["fastapi-users:auth"])
    return int(encoded_jwt['sub'])

@router.websocket("/ws/{receiver_username}")
async def websocket_endpoint(
    websocket: WebSocket,
    receiver_username: str,
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    await websocket.accept()
    user_id = (await get_user_id_from_jwt(token))
    
    # Получаем информацию об отправителе
    query = select(User).where(User.id == user_id)
    result = (await session.execute(query)).scalars().all()[0]
    sender_username = result.username
    sender_id = result.id
    active_connections[sender_id] = websocket
    try:
        # Получение сообщений для пользователя при подключении
        
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
                print('Receiver not online')
                new_message = MessageAdd(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    content=message,
                    is_read=False
                )
            else:
                print('Receiver online')
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
        print(f"Client {sender_username} disconnected")

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
        formatted_time = message.created_at.strftime("%Y-%m-%d %H:%M:%S")  # Форматируем время
        if message.sender_id == sender_id:
            await websocket.send_text(
                f"[{formatted_time}] you : {message.content}"
            )
        else:
            await websocket.send_text(
                f"[{formatted_time}] {receiver}: {message.content}"
            )

async def send_message_to_recipient(receiver_id: int, sender_username : str, message: str):
    # Здесь вы можете реализовать логику отправки сообщения получателю.
    # Например, сохраните WebSocket для каждого пользователя и используйте его для отправки сообщений.
    # Например, можно использовать словарь для хранения WebSocket-соединений:
    if receiver_id in active_connections:
        recipient_websocket = active_connections[receiver_id]
        await recipient_websocket.send_text(f"[NOW] {sender_username} : {message}")