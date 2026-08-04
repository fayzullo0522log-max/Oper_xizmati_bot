import asyncio
import logging
from aiogram import Router, F
from aiogram.types import (
    ChatMemberUpdated,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

import database as db

router = Router()
logger = logging.getLogger(__name__)

'CAPTCHA_TIMEOUT_SECONDS'

@router.chat_member()
async def on_member_join(event: ChatMemberUpdated):
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    joined_statuses = {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}
    if old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED) and new_status in joined_statuses:
        chat_id = event.chat.id
        user = event.new_chat_member.user
        if user.is_bot:
            return

        await db.ensure_group_settings(chat_id)
        await db.ensure_group_member(chat_id, user.id)
        await db.upsert_user(user.id, user.username or "", user.first_name or "")

        settings = await db.get_settings(chat_id)
        bot = event.bot

        if settings["captcha_enabled"]:
            try:
                await bot.restrict_chat_member(
                    chat_id,
                    user.id,
                    permissions={"can_send_messages": False},
                )
            except TelegramBadRequest as e:
                logger.warning(f"Restrict qila olmadi: {e}")

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="✅ Men robot emasman",
                        callback_data=f"captcha_ok:{user.id}",
                    )
                ]]
            )
            msg = await bot.send_message(
                chat_id,
                f"👋 Xush kelibsiz, {user.first_name}!\n\n"
                f"Guruhda yozish uchun pastdagi tugmani bosing."
                reply_markup=keyboard,
            )
        else:
            welcome = settings.get("welcome_message") or f"👋 Xush kelibsiz, {user.first_name}!"
            await bot.send_message(chat_id, welcome)


async def _captcha_timeout(bot, chat_id: int, user_id: int, message_id: int):
    await asyncio.sleep(CAPTCHA_TIMEOUT_SECONDS)
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.RESTRICTED:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
            await bot.delete_message(chat_id, message_id)
            await bot.send_message(
                chat_id, f"⏱ Vaqt tugadi, foydalanuvchi guruhdan chiqarildi."
            )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("captcha_ok:"))
async def on_captcha_pass(callback: CallbackQuery):
    target_user_id = int(callback.data.split(":")[1])
    if callback.from_user.id != target_user_id:
        await callback.answer("Bu captcha siz uchun emas.", show_alert=True)
        return

    chat_id = callback.message.chat.id
    try:
        await callback.bot.restrict_chat_member(
            chat_id,
            target_user_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
            },
        )
    except TelegramBadRequest as e:
        logger.warning(f"Ruxsat qaytarib bo'lmadi: {e}")

    settings = await db.get_settings(chat_id)
    await callback.message.edit_text("✅ Tasdiqlandi! Xush kelibsiz.")
    if settings["rules_text"]:
        await callback.message.answer(f"📜 Guruh qoidalari:\n{settings['rules_text']}")
    await callback.answer("Rahmat!")
