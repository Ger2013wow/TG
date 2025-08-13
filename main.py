import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ChatMemberUpdated
)
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
JOIN_REQUEST_LINK = os.getenv("JOIN_REQUEST_LINK", "").strip()
WELCOME_DM_TEXT = os.getenv(
    "WELCOME_DM_TEXT",
    "👋 Добро пожаловать!\n🎁 Бонус-код: WEPARI2025\nУсловия: вейджер x30..."
)

if not BOT_TOKEN or not GROUP_ID or not JOIN_REQUEST_LINK:
    raise SystemExit("Set BOT_TOKEN, GROUP_ID, JOIN_REQUEST_LINK env vars")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def kb_join() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Вступить в группу", url=JOIN_REQUEST_LINK)]
    ])

@dp.message(CommandStart())
async def on_start(m: Message):
    await m.answer(
        "Привет! Нажми «Вступить в группу». После вступления пришлю сообщение в личку.",
        reply_markup=kb_join()
    )

@dp.chat_member()
async def on_chat_member(update: ChatMemberUpdated):
    # Ловим факт вступления в нужную группу
    if update.chat.id != GROUP_ID:
        return
    if (
        update.new_chat_member.status == ChatMemberStatus.MEMBER and
        update.old_chat_member.status != ChatMemberStatus.MEMBER
    ):
        user = update.new_chat_member.user
        await try_dm_or_fallback(user.id, user.full_name)

async def try_dm_or_fallback(user_id: int, full_name: str):
    try:
        await bot.send_message(user_id, WELCOME_DM_TEXT)
    except TelegramForbiddenError:
        # Юзер не нажал Start — отправим подсказку в группу
        mention = f"<a href='tg://user?id={user_id}'>{full_name}</a>"
        msg = f"{mention}, откройте чат с ботом @wepari_tr_bot и нажмите /start, чтобы получить бонус."
        try:
            await bot.send_message(GROUP_ID, msg, disable_web_page_preview=True)
        except Exception:
            pass

async def main():
    me = await bot.get_me()
    print(f"Started @{me.username} | GROUP_ID={GROUP_ID}")
    await dp.start_polling(bot, allowed_updates=["message", "chat_member"])

if __name__ == "__main__":
    asyncio.run(main())
