# pip install aiogram==2.25.1
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ===== Совместимость с "прошлым" ботом =====
BOT_TOKEN = (
    os.getenv("TELEGRAM_BOT_TOKEN")      # как было раньше
    or os.getenv("BOT_TOKEN")            # альтернативно
    or os.getenv("TOKEN")                # на всякий случай
)
if not BOT_TOKEN:
    raise RuntimeError("Не найден токен: TELEGRAM_BOT_TOKEN / BOT_TOKEN / TOKEN")

# Поддерживаем несколько вариантов переменных с chat id из прошлого бота
def collect_chat_ids():
    ids = set()
    # Универсальные:
    for name in ["CHAT_ID", "GROUP_ID", "CHANNEL_ID"]:
        v = os.getenv(name)
        if v:
            ids.add(int(v))

    # Список через запятую:
    for name in ["CHAT_IDS", "GROUP_IDS", "CHANNEL_IDS"]:
        v = os.getenv(name)
        if v:
            for part in v.split(","):
                part = part.strip()
                if part:
                    ids.add(int(part))

    # Языковые/региональные (как раньше):
    for name in [
        "GROUP_ID_RU", "GROUP_ID_EN", "GROUP_ID_TR", "GROUP_ID_AZ", "GROUP_ID_ES",
        "GROUP_ID_AR", "GROUP_ID_KZ", "GROUP_ID_UA"
    ]:
        v = os.getenv(name)
        if v:
            ids.add(int(v))

    return ids

TARGET_CHAT_IDS = collect_chat_ids()
# Если пусто — работаем в режиме «определи id в логах»
DISCOVERY_MODE = len(TARGET_CHAT_IDS) == 0

# Кнопки: "Текст|URL;Текст2|URL2"
RAW_BUTTONS = os.getenv("BUTTONS", "Перейти 🌐|https://wepari.com")
BUTTON_HEADER_TEXT = os.getenv("BUTTON_HEADER_TEXT", "👉 Кнопка для поста выше")
ROW_WIDTH = int(os.getenv("BUTTON_ROW_WIDTH", "1"))  # 1 = столбиком, 2 = по две в ряд

def parse_buttons(raw: str):
    buttons = []
    for chunk in (raw or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "|" in chunk:
            txt, url = chunk.split("|", 1)
            buttons.append({"text": txt.strip(), "url": url.strip()})
        else:
            # fallback: если без |, используем и как текст, и как url
            buttons.append({"text": chunk, "url": chunk})
    return buttons

BUTTONS = parse_buttons(RAW_BUTTONS)

# ===== Бот =====
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

def make_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=ROW_WIDTH)
    for b in BUTTONS:
        if not b.get("text") or not b.get("url"):
            continue
        kb.add(types.InlineKeyboardButton(text=b["text"], url=b["url"]))
    return kb

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def attach_buttons(message: types.Message):
    # Если мы в режиме поиска chat id — просто логируем
    if DISCOVERY_MODE:
        print(f"[DISCOVERY] chat id: {message.chat.id} | title: {message.chat.title}")
        return

    # Только целевые чаты
    if message.chat.id not in TARGET_CHAT_IDS:
        return

    # Игнор ботов (включая себя)
    if message.from_user and message.from_user.is_bot:
        return

    # Отправляем ответ с кнопками «под» исходным постом
    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=BUTTON_HEADER_TEXT,
            reply_markup=make_keyboard(),
            reply_to_message_id=message.message_id
        )
    except Exception as e:
        print(f"[ERROR] failed to send buttons: {e}")

if __name__ == "__main__":
    print("Buttons relay bot started (long polling).")
    if DISCOVERY_MODE:
        print("DISCOVERY_MODE=ON → напишите что-нибудь в нужной группе, в логах появится её chat id.")
    else:
        print(f"Watching chat ids: {sorted(TARGET_CHAT_IDS)}")
    from aiogram import executor as ex
    ex.start_polling(dp, skip_updates=True)
