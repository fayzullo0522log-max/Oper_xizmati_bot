import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

SUPER_ADMINS = set(
    int(x.strip()) for x in os.getenv("SUPER_ADMINS", "").split(",") if x.strip()
)

FLOOD_MESSAGE_LIMIT = int(os.getenv("FLOOD_MESSAGE_LIMIT", 5))
FLOOD_TIME_WINDOW = int(os.getenv("FLOOD_TIME_WINDOW", 5))
FLOOD_MUTE_MINUTES = int(os.getenv("FLOOD_MUTE_MINUTES", 10))

MAX_WARNS = int(os.getenv("MAX_WARNS", 3))

DB_PATH = "bot_database.db"

# Standart taqiqlangan so'zlar (kerak bo'lsa /addword orqali guruhga qo'shiladi)
DEFAULT_BANNED_WORDS = [
    "казино", "casino", "порно", "porn", "crypto airdrop",
    "заработок без вложений", "kredit tez", "bepul pul yutish",
]

# Ruxsat etilgan domenlar (masalan, o'z kanalingiz), qolgan havolalar filtrlanadi
WHITELISTED_DOMAINS = [
    "t.me",  # kerak bo'lsa o'zgartiring yoki bo'shating
]
