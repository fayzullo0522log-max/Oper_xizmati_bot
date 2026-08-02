import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

import database as db
from config import MAX_WARNS, FLOOD_MUTE_MINUTES
from filters.flood_filter import is_flooding, reset_user
from filters.spam_filter import contains_link, contains_whitelisted_only, contains_banned_word

router = Router()
logger = logging.getLogger(__name__)


async def _is_admin(message: Message) -> bool:
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR)


async def _apply_warn_or_punish(message: Message, reason: str):
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    warn_count = await db.add_warn(chat_id, user_id)

    if warn_count >= MAX_WARNS:
        try:
            await message.bot.ban_chat_member(chat_id, user_id)
            await db.set_banned(chat_id, user_id, True)
            await message.answer(
                f"🚫 {message.from_user.full_name} bloklandi "
                f"({MAX_WARNS} marta ogohlantirishdan keyin).\nSabab: {reason}"
            )
        except TelegramBadRequest as e:
            logger.warning(f"Ban qila olmadi: {e}")
    else:
        await message.answer(
            f"⚠️ {message.from_user.full_name}, xabaringiz o'chirildi.\n"
            f"Sabab: {reason}\nOgohlantirish: {warn_count}/{MAX_WARNS}"
        )


async def _mute_for_flood(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    until = datetime.utcnow() + timedelta(minutes=FLOOD_MUTE_MINUTES)

    try:
        await message.bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions={"can_send_messages": False},
            until_date=until,
        )
        await message.answer(
            f"🔇 {message.from_user.full_name} spam (flood) tufayli "
            f"{FLOOD_MUTE_MINUTES} daqiqaga jim qilindi."
        )
        reset_user(chat_id, user_id)
    except TelegramBadRequest as e:
        logger.warning(f"Mute qila olmadi: {e}")


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def moderate_message(message: Message):
    if not message.from_user or message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    await db.ensure_group_settings(chat_id)
    await db.ensure_group_member(chat_id, user_id)
    await db.upsert_user(user_id, message.from_user.username or "", message.from_user.first_name or "")

    if await _is_admin(message):
        return

    settings = await db.get_settings(chat_id)
    text = message.text or message.caption or ""

    if settings["flood_filter_enabled"] and is_flooding(chat_id, user_id):
        await _mute_for_flood(message)
        return

    banned_words = await db.get_banned_words(chat_id)
    found_word = contains_banned_word(text, banned_words)
    if found_word:
        await _apply_warn_or_punish(message, f"taqiqlangan so'z ishlatildi")
        return

    if settings["link_filter_enabled"] and contains_link(text):
        if not contains_whitelisted_only(text):
            await _apply_warn_or_punish(message, "ruxsatsiz havola yuborish")
            return
