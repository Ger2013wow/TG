# pip install aiogram==2.25.1
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # вставь сюда новый токен, если не используешь переменные окружения!
if not BOT_TOKEN:
    raise RuntimeError("❌ Укажи токен бота в BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

keyboard = types.InlineKeyboardMarkup()
keyboard.add(types.InlineKeyboardButton("ЛОМАЙ МЕНЯ", url="https://ya.ru"))

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def add_button(message: types.Message):
    if message.from_user and message.from_user.is_bot:
        return
    await bot.send_message(
        chat_id=message.chat.id,
        text="👉 Нажми кнопку ниже",
        reply_markup=keyboard,
        reply_to_message_id=message.message_id
    )

if __name__ == "__main__":
    print("🚀 Bot started. Listening…")
    executor.start_polling(dp, skip_updates=True)
