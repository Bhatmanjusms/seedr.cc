import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SEEDR_USERNAME = os.getenv("SEEDR_USERNAME")
SEEDR_PASSWORD = os.getenv("SEEDR_PASSWORD")
