from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
TGBOT_TOKEN_ADMIN = os.environ.get('TGBOT_TOKEN_ADMIN')
TG_ID_ADMIN = os.environ.get('TG_ID_ADMIN')
SECRET_JWT = os.environ.get('SECRET_JWT')
NOTIFICATIONS_TGBOT_TOKEN = os.environ.get('NOTIFICATIONS_TGBOT_TOKEN')