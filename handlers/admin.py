import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

import database as db

router = Router()
logger = logging.getLogger(__name__)


async def _require_admin(message: Message) -> bool:
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR):
        await message.reply("❌ Bu buyruq faqat adminlar uchun.")
        return False
    return True


def _get_target_user_id(message: Message) -> int | None:
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    return None


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob (reply) qilib /ban yozing.")
        return
    try:
        await message.bot.ban_chat_member(message.chat.id, target_id)
        await db.set_banned(message.chat.id, target_id, True)
        await message.reply("🚫 Foydalanuvchi bloklandi.")
    except TelegramBadRequest as e:
        await message.reply(f"Xatolik: {e}")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob qilib /unban yozing.")
        return
    try:
        await message.bot.unban_chat_member(message.chat.id, target_id)
        await db.set_banned(message.chat.id, target_id, False)
        await db.reset_warns(message.chat.id, target_id)
        await message.reply("✅ Blok olib tashlandi.")
    except TelegramBadRequest as e:
        await message.reply(f"Xatolik: {e}")


@router.message(Command("kick"))
async def cmd_kick(message: Message):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob qilib /kick yozing.")
        return
    try:
        await message.bot.ban_chat_member(message.chat.id, target_id)
        await message.bot.unban_chat_member(message.chat.id, target_id)
        await message.reply("👢 Foydalanuvchi guruhdan chiqarildi.")
    except TelegramBadRequest as e:
        await message.reply(f"Xatolik: {e}")


@router.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob qilib /mute [daqiqa] yozing.")
        return

    minutes = 60
    if command.args and command.args.strip().isdigit():
        minutes = int(command.args.strip())

    until = datetime.utcnow() + timedelta(minutes=minutes)
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            target_id,
            permissions={"can_send_messages": False},
            until_date=until,
        )
        await message.reply(f"🔇 Foydalanuvchi {minutes} daqiqaga jim qilindi.")
    except TelegramBadRequest as e:
        await message.reply(f"Xatolik: {e}")


@router.message(Command("unmute"))
async def cmd_unmute(message: Message):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob qilib /unmute yozing.")
        return
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            target_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
            },
        )
        await message.reply("🔊 Foydalanuvchiga yozish ruxsati qaytarildi.")
    except TelegramBadRequest as e:
        await message.reply(f"Xatolik: {e}")


@router.message(Command("warn"))
async def cmd_warn(message: Message):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob qilib /warn yozing.")
        return
    await db.ensure_group_member(message.chat.id, target_id)
    count = await db.add_warn(message.chat.id, target_id)
    await message.reply(f"⚠️ Ogohlantirish berildi ({count}/3).")


@router.message(Command("resetwarn"))
async def cmd_resetwarn(message: Message):
    if not await _require_admin(message):
        return
    target_id = _get_target_user_id(message)
    if not target_id:
        await message.reply("Foydalanuvchi xabariga javob qilib /resetwarn yozing.")
        return
    await db.reset_warns(message.chat.id, target_id)
    await message.reply("✅ Ogohlantirishlar tozalandi.")


@router.message(Command("addword"))
async def cmd_addword(message: Message, command: CommandObject):
    if not await _require_admin(message):
        return
    if not command.args:
        await message.reply("Foydalanish: /addword taqiqlangan_soz")
        return
    word = command.args.strip().lower()
    await db.add_banned_word(message.chat.id, word)
    await message.reply(f"✅ '{word}' taqiqlangan so'zlar ro'yxatiga qo'shildi.")


@router.message(Command("removeword"))
async def cmd_removeword(message: Message, command: CommandObject):
    if not await _require_admin(message):
        return
    if not command.args:
        await message.reply("Foydalanish: /removeword soz")
        return
    word = command.args.strip().lower()
    await db.remove_banned_word(message.chat.id, word)
    await message.reply(f"✅ '{word}' ro'yxatdan olib tashlandi.")


@router.message(Command("wordlist"))
async def cmd_wordlist(message: Message):
    if not await _require_admin(message):
        return
    words = await db.get_banned_words(message.chat.id)
    if not words:
        await message.reply("Taqiqlangan so'zlar yo'q.")
        return
    await message.reply("🚫 Taqiqlangan so'zlar:\n" + ", ".join(words))


@router.message(Command("setrules"))
async def cmd_setrules(message: Message, command: CommandObject):
    if not await _require_admin(message):
        return
    if not command.args:
        await message.reply("Foydalanish: /setrules Guruh qoidalari matni...")
        return
    await db.set_rules(message.chat.id, command.args)
    await message.reply("✅ Qoidalar saqlandi.")


@router.message(Command("rules"))
async def cmd_rules(message: Message):
    rules = await db.get_rules(message.chat.id)
    if not rules:
        await message.reply("Qoidalar hali belgilanmagan.")
        return
    await message.reply(f"📜 Guruh qoidalari:\n{rules}")


@router.message(Command("captcha_on"))
async def cmd_captcha_on(message: Message):
    if not await _require_admin(message):
        return
    await db.toggle_setting(message.chat.id, "captcha_enabled", True)
    await message.reply("✅ Captcha yoqildi.")


@router.message(Command("captcha_off"))
async def cmd_captcha_off(message: Message):
    if not await _require_admin(message):
        return
    await db.toggle_setting(message.chat.id, "captcha_enabled", False)
    await message.reply("✅ Captcha o'chirildi.")


@router.message(Command("linkfilter_on"))
async def cmd_linkfilter_on(message: Message):
    if not await _require_admin(message):
        return
    await db.toggle_setting(message.chat.id, "link_filter_enabled", True)
    await message.reply("✅ Havola filtri yoqildi.")


@router.message(Command("linkfilter_off"))
async def cmd_linkfilter_off(message: Message):
    if not await _require_admin(message):
        return
    await db.toggle_setting(message.chat.id, "link_filter_enabled", False)
    await message.reply("✅ Havola filtri o'chirildi.")


@router.message(Command("floodfilter_on"))
async def cmd_floodfilter_on(message: Message):
    if not await _require_admin(message):
        return
    await db.toggle_setting(message.chat.id, "flood_filter_enabled", True)
    await message.reply("✅ Flood filtri yoqildi.")


@router.message(Command("floodfilter_off"))
async def cmd_floodfilter_off(message: Message):
    if not await _require_admin(message):
        return
    await db.toggle_setting(message.chat.id, "flood_filter_enabled", False)
    await message.reply("✅ Flood filtri o'chirildi.")


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    if not await _require_admin(message):
        return
    s = await db.get_settings(message.chat.id)
    text = (
        "⚙️ Guruh sozlamalari:\n\n"
        f"Captcha: {'✅ yoqilgan' if s['captcha_enabled'] else '❌ ochirilgan'}\n"
        f"Havola filtri: {'✅ yoqilgan' if s['link_filter_enabled'] else '❌ ochirilgan'}\n"
        f"Flood filtri: {'✅ yoqilgan' if s['flood_filter_enabled'] else '❌ ochirilgan'}\n"
    )
    await message.reply(text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "🤖 <b>Guruh boshqaruv boti — buyruqlar</b>\n\n"
        "<b>Moderatsiya (xabarga reply qilib yozing):</b>\n"
        "/ban — bloklash\n"
        "/unban — blokdan chiqarish\n"
        "/kick — guruhdan chiqarish\n"
        "/mute [daqiqa] — jim qilish\n"
        "/unmute — jimlikni bekor qilish\n"
        "/warn — ogohlantirish berish\n"
        "/resetwarn — ogohlantirishlarni tozalash\n\n"
        "<b>So'zlar ro'yxati:</b>\n"
        "/addword so'z — taqiqlash\n"
        "/removeword so'z — ro'yxatdan olish\n"
        "/wordlist — ro'yxatni ko'rish\n\n"
        "<b>Qoidalar:</b>\n"
        "/setrules matn — qoida o'rnatish\n"
        "/rules — qoidani ko'rish\n\n"
        "<b>Sozlamalar:</b>\n"
        "/captcha_on /captcha_off\n"
        "/linkfilter_on /linkfilter_off\n"
        "/floodfilter_on /floodfilter_off\n"
        "/settings — joriy holatni ko'rish"
    )
    await message.reply(text, parse_mode="HTML")
