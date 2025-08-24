 
# fincontrol/bot/config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8386237598:AAGXOcisrleIeyCoC6UAXnPgnXohTc1YDEc")
