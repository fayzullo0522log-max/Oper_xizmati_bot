import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply(
        "👋 Salom! Men guruh moderatsiya boti.\n\n"
        "Meni guruhingizga admin qilib qo'shing, "
        "shunda captcha, moderatsiya va boshqa funksiyalardan foydalanishingiz mumkin."
    )
