import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ChatJoinRequest,
)
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
JOIN_REQUEST_LINK = os.getenv("JOIN_REQUEST_LINK", "").strip()

WELCOME_DM_TEXT = os.getenv("WELCOME_DM_TEXT", (
    "👋 Добро пожаловать!\n"
    "🎁 Бонус-код: WEPARI2025\n"
    "Условия: вейджер x30. Код общий, действует для всех участников группы.\n\n"
    "Как применить:\n"
    "1) Зайдите в личный кабинет.\n"
    "2) Введите код при пополнении.\n"
    "3) Бонус начислится автоматически."
))

if not BOT_TOKEN:
    raise SystemExit("Set BOT_TOKEN env var")
if not GROUP_ID:
    raise SystemExit("Set GROUP_ID env var (e.g. -1001234567890)")
if not JOIN_REQUEST_LINK:
    raise SystemExit("Set JOIN_REQUEST_LINK env var (https://t.me/+XXXX join-request link)")

bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

def kb_join() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Вступить в группу", url=JOIN_REQUEST_LINK)]
    ])

@dp.message(CommandStart())
async def on_start(m: Message):
    first = m.from_user.first_name or "друг"
    text = (
        f"Привет, {first}! 🎉\n\n"
        "Чтобы получить бонус и автоматическое сообщение — вступай в нашу группу.\n"
        "Нажми «Вступить в группу» ниже. Заявку одобрим автоматически."
    )
    await m.answer(text, reply_markup=kb_join())

@dp.chat_join_request()
async def on_join_request(req: ChatJoinRequest):
    user = req.from_user
    user_id = user.id

    try:
        await bot.approve_chat_join_request(chat_id=req.chat.id, user_id=user_id)
    except TelegramBadRequest as e:
        print(f"[WARN] approve_chat_join_request: {e}")

    try:
        await bot.send_message(chat_id=user_id, text=WELCOME_DM_TEXT)
    except TelegramForbiddenError:
        try:
            mention = f"<a href='tg://user?id={user_id}'>{user.full_name}</a>"
            msg = (
                f"{mention}, откройте чат с ботом @wepari_tr_bot и нажмите /start, "
                f"чтобы получить бонус-код в личку."
            )
            await bot.send_message(chat_id=GROUP_ID, text=msg, disable_web_page_preview=True)
        except Exception:
            pass
    except Exception as e:
        print(f"[ERROR] send DM failed: {e}")

async def main():
    me = await bot.get_me()
    print(f"Started @{me.username} | GROUP_ID={GROUP_ID}")
    await dp.start_polling(bot, allowed_updates=["message", "chat_join_request"])

if __name__ == "__main__":
    asyncio.run(main())