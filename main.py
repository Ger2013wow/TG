# aiogram 3.7+ — respond to human, other bots, and anonymous admin (sender_chat), but skip our own messages
import os, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.enums import ParseMode, ChatType
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ Set BOT_TOKEN")

RAW_CHAT_IDS = os.getenv("CHAT_IDS") or os.getenv("GROUP_IDS") or os.getenv("CHAT_ID") or ""
WATCH_CHAT_IDS = {int(x.strip()) for x in str(RAW_CHAT_IDS).split(",") if x.strip()}
DISCOVERY_MODE = len(WATCH_CHAT_IDS) == 0

BUTTON_TEXT = os.getenv("BUTTON_TEXT", "ЛОМАЙ МЕНЯ")
BUTTON_URL  = os.getenv("BUTTON_URL", "https://ya.ru")
BUTTON_HEADER_TEXT = os.getenv("BUTTON_HEADER_TEXT", "👉 Oyuna davam et, WePari hər həftə sənə dəstək olsun!")
REPLY_MODE = os.getenv("REPLY_MODE", "false").lower() in {"1","true","yes","y"}

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BUTTON_TEXT, url=BUTTON_URL)]])

async def send_button_message(msg: Message, source: str):
    me = await bot.get_me()

    if DISCOVERY_MODE:
        print(f"[DISCOVERY] chat id: {msg.chat.id} | title: {msg.chat.title} | from {source}")
        return
    if msg.chat.id not in WATCH_CHAT_IDS:
        print(f"[SKIP] unseen chat {msg.chat.id} ({msg.chat.title}) | expected {sorted(WATCH_CHAT_IDS)} | from {source}")
        return

    # ⚠️ Пропускаем только СВОИ сообщения, чтобы не зациклиться
    if msg.from_user and msg.from_user.id == me.id:
        print(f"[SKIP] own bot message loop | from {source}")
        return
    # Если сообщение «от имени чата» (анонимный админ / канал) — обрабатываем:
    # msg.sender_chat is not None → значит это пост от лица группы/канала.

    kwargs = dict(chat_id=msg.chat.id, text=BUTTON_HEADER_TEXT, reply_markup=kb())
    if REPLY_MODE and msg.message_id:
        kwargs["reply_to_message_id"] = msg.message_id

    try:
        await bot.send_message(**kwargs)
        print(f"[OK] sent button in {msg.chat.id} ({msg.chat.title}) | reply={REPLY_MODE} | from {source}")
    except Exception as e:
        print(f"[ERROR] cannot send: {type(e).__name__}: {e}")

@dp.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def on_group_message(msg: Message):
    await send_button_message(msg, source="message")

@dp.channel_post()
async def on_channel_post(msg: Message):
    await send_button_message(msg, source="channel_post")

@dp.message(F.chat.type == ChatType.PRIVATE)
async def on_private(msg: Message):
    await send_button_message(msg, source="private")

async def main():
    print(f"🚀 Buttons relay bot started. Reply mode: {REPLY_MODE}")
    if DISCOVERY_MODE:
        print("DISCOVERY_MODE=ON → напишите в целевой чат, id появится в логах.")
    else:
        print(f"Watching chat ids: {sorted(WATCH_CHAT_IDS)}")
    await dp.start_polling(bot, allowed_updates=["message","channel_post"])

if __name__ == "__main__":
    asyncio.run(main())
