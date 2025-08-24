
import os, asyncio, sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from texts import TEXTS

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is missing. Set it in Railway Variables.")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

ALL_LANGS = ("en", "ru", "tr", "az", "es")

def detect_lang_from_tg(code: str | None) -> str:
    if not code:
        return "en"
    c = code.split("-")[0].lower()
    return c if c in ALL_LANGS else "en"

def lang_bucket(lang: str) -> str:
    return lang if lang in ("tr", "az", "es") else "other"

GROUP = {
    "tr": int(os.getenv("GROUP_TR_ID", "0")),
    "az": int(os.getenv("GROUP_AZ_ID", "0")),
    "es": int(os.getenv("GROUP_ES_ID", "0")),
    "other": int(os.getenv("GROUP_OTHER_ID", "0")),
}

CODE = {
    "tr": os.getenv("LANG_CODE_TR", "WelcomeTR200"),
    "az": os.getenv("LANG_CODE_AZ", "WelcomeAZ200"),
    "es": os.getenv("LANG_CODE_ES", "WelcomeAR200"),
    "other": os.getenv("LANG_CODE_OTHER", "Welcome200"),
}

DB = "promo.db"
def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS sent_log(
        user_id INTEGER, bucket TEXT,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, bucket)
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS user_lang(
        user_id INTEGER PRIMARY KEY,
        lang TEXT
    )""")
    return con

def get_saved_lang(user_id: int) -> str | None:
    con = db(); cur = con.cursor()
    cur.execute("SELECT lang FROM user_lang WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def save_lang(user_id: int, lang: str):
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO user_lang(user_id, lang) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang", (user_id, lang))
    con.commit(); con.close()

def already_sent(user_id: int, bucket: str) -> bool:
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM sent_log WHERE user_id=? AND bucket=?", (user_id, bucket))
    ok = cur.fetchone() is not None
    con.close(); return ok

def mark_sent(user_id: int, bucket: str):
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO sent_log(user_id, bucket) VALUES(?,?)", (user_id, bucket))
    con.commit(); con.close()

def pick_lang(user_id: int, payload: str | None, tg_lang_code: str | None) -> str:
    if payload and payload in ALL_LANGS:
        return payload
    saved = get_saved_lang(user_id)
    if saved in ALL_LANGS:
        return saved
    return detect_lang_from_tg(tg_lang_code)

USER_LANG = {}

def language_buttons():
    return [
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en"),
         InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru")],
        [InlineKeyboardButton(text="Türkçe 🇹🇷", callback_data="lang:tr"),
         InlineKeyboardButton(text="Azərbaycan 🇦🇿", callback_data="lang:az"),
         InlineKeyboardButton(text="Español 🇪🇸", callback_data="lang:es")]
    ]

def main_menu_kb(display_lang: str, invite_link: str | None):
    rows = []
    if invite_link:
        rows.append([InlineKeyboardButton(text=TEXTS["join_btn"][display_lang], url=invite_link)])
    rows += language_buttons()
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def make_invite(bucket: str) -> str | None:
    gid = GROUP.get(bucket, 0)
    if not gid:
        return None
    try:
        inv = await bot.create_chat_invite_link(chat_id=gid, name=f"promo-{bucket}", creates_join_request=False)
        return inv.invite_link
    except Exception as e:
        print(f"[invite] failed for {bucket}: {e}")
        return None

def reverse_group_map():
    rev = {}
    for b, gid in GROUP.items():
        rev.setdefault(gid, []).append(b)
    return rev

@dp.message(CommandStart())
async def on_start(m: Message):
    payload = ""
    if " " in m.text:
        payload = m.text.split(" ", 1)[1].strip().lower()

    display_lang = pick_lang(m.from_user.id, payload, m.from_user.language_code)
    USER_LANG[m.from_user.id] = display_lang
    save_lang(m.from_user.id, display_lang)

    bucket = lang_bucket(display_lang)
    invite = await make_invite(bucket)
    kb = main_menu_kb(display_lang, invite)
    await m.answer(TEXTS["welcome"][display_lang], reply_markup=kb)

@dp.callback_query(F.data.startswith("lang:"))
async def on_lang_change(cq: CallbackQuery):
    display_lang = cq.data.split(":")[1]
    if display_lang not in ALL_LANGS:
        display_lang = "en"
    USER_LANG[cq.from_user.id] = display_lang
    save_lang(cq.from_user.id, display_lang)

    bucket = lang_bucket(display_lang)
    invite = await make_invite(bucket)
    kb = main_menu_kb(display_lang, invite)
    await cq.message.edit_text(TEXTS["welcome"][display_lang], reply_markup=kb)
    await cq.answer(TEXTS["lang_switched"][display_lang])

@dp.chat_member()
async def on_join(evt: ChatMemberUpdated):
    if evt.new_chat_member.status != "member":
        return
    user = evt.new_chat_member.user
    display_lang = USER_LANG.get(user.id, get_saved_lang(user.id) or "en")

    rev = reverse_group_map()
    candidates = rev.get(evt.chat.id, [])
    if len(candidates) == 1:
        bucket = candidates[0]
    else:
        bucket = lang_bucket(display_lang)

    code = CODE.get(bucket)
    if not code:
        return

    if already_sent(user.id, bucket):
        txt = TEXTS["already_sent"][display_lang].replace("{CODE}", code)
    else:
        txt = TEXTS["code_dm"][display_lang].replace("{CODE}", code)

    try:
        await bot.send_message(user.id, txt, parse_mode="Markdown")
        mark_sent(user.id, bucket)
    except Exception as e:
        print(f"[dm] failed to {user.id}: {e}")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
