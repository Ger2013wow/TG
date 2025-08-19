# aiogram 3.7+ (Python 3.12) — non-reply button message
import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.enums import ParseMode, ChatType
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ Set BOT_TOKEN env var")

RAW_CHAT_IDS = os.getenv("CHAT_IDS") or os.getenv("GROUP_IDS") or os.getenv("CHAT_ID") or ""
WATCH_CHAT_IDS = set()
for part in str(RAW_CHAT_IDS).split(","):
    part = part.strip()
    if part:
        try:
            WATCH_CHAT_IDS.add(int(part))
        except ValueError:
            pass
DISCOVERY_MODE = len(WATCH_CHAT_IDS) == 0

BUTTON_TEXT = os.getenv("BUTTON_TEXT", "ЛОМАЙ МЕНЯ")
BUTTON_URL  = os.getenv("BUTTON_URL", "https://ya.ru")
BUTTON_HEADER_TEXT = os.getenv("BUTTON_HEADER_TEXT", "WeWin WePlay WePari")
# Управляет стилем: true = отвечать на пост (reply), false = просто новое сообщение
REPLY_MODE = os.getenv("REPLY_MODE", "false").lower() in {"1","true","yes","y"}

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def make_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BUTTON_TEXT, url=BUTTON_URL)]])

@dp.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL, ChatType.PRIVATE}))
async def on_any_message(msg: Message):
    if DISCOVERY_MODE:
        print(f"[DISCOVERY] chat id: {msg.chat.id} | title: {msg.chat.title}")
        return
    if msg.chat.id not in WATCH_CHAT_IDS:
        return
    if msg.from_user and msg.from_user.is_bot:
        return

    kwargs = dict(chat_id=msg.chat.id, text=BUTTON_HEADER_TEXT, reply_markup=make_keyboard())
    if REPLY_MODE:
        kwargs["reply_to_message_id"] = msg.message_id
    try:
        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[ERROR] {e}")

async def main():
    print("🚀 Buttons relay bot started. Reply mode:", REPLY_MODE)
    if DISCOVERY_MODE:
        print("DISCOVERY_MODE=ON → write in your chat; id will appear here.")
    else:
        print(f"Watching chat ids: {sorted(WATCH_CHAT_IDS)}")
    await dp.start_polling(bot, allowed_updates=["message","channel_post"])

if __name__ == "__main__":
    asyncio.run(main())
