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
    con.execute("""CREATE TABLE IF NOT EXISTS user_code(
        user_id INTEGER PRIMARY KEY,
        code TEXT,
        first_bucket TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    return con

def get_assigned_code(user_id: int) -> str | None:
    con = db(); cur = con.cursor()
    cur.execute("SELECT code FROM user_code WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else None

def assign_code(user_id: int, bucket: str) -> str:
    code = CODE.get(bucket) or CODE.get("other") or "Welcome200"
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO user_code(user_id, code, first_bucket) VALUES(?,?,?)", (user_id, code, bucket))
    con.commit(); con.close()
    return code

def already_sent_any(user_id: int) -> bool:
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM sent_log WHERE user_id=? LIMIT 1", (user_id,))
    ok = cur.fetchone() is not None
    con.close(); return ok

def mark_sent(user_id: int, bucket: str):
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO sent_log(user_id, bucket) VALUES(?,?)", (user_id, bucket))
    con.commit(); con.close()

USER_LANG = {}

def language_buttons():
    return [
        [
            InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en"),
            InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru"),
        ],
        [
            InlineKeyboardButton(text="Türkçe 🇹🇷", callback_data="lang:tr"),
            InlineKeyboardButton(text="Azərbaycan 🇦🇿", callback_data="lang:az"),
            InlineKeyboardButton(text="Español 🇪🇸", callback_data="lang:es"),
        ],
    ]

def main_menu_kb(display_lang: str, invite_link: str | None):
    rows = []
    if invite_link:
        rows.append([InlineKeyboardButton(text=TEXTS["join_btn"][display_lang], url=invite_link)])
    rows.append([InlineKeyboardButton(text=TEXTS["im_in_btn"][display_lang], callback_data="im_in")])
    rows += language_buttons()
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def get_invite_link(bucket: str) -> str | None:
    gid = GROUP.get(bucket, 0)
    if not gid:
        return None
    try:
        inv = await bot.create_chat_invite_link(chat_id=gid, name=f"promo-{bucket}", creates_join_request=False)
        return inv.invite_link
    except Exception as e:
        print(f"[invite:create] failed for {bucket}: {e}")
    try:
        link = await bot.export_chat_invite_link(chat_id=gid)
        return link
    except Exception as e:
        print(f"[invite:export] failed for {bucket}: {e}")
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
    display_lang = payload if payload in ALL_LANGS else detect_lang_from_tg(m.from_user.language_code)
    USER_LANG[m.from_user.id] = display_lang

    bucket = lang_bucket(display_lang)
    invite = await get_invite_link(bucket)
    kb = main_menu_kb(display_lang, invite)
    await m.answer(TEXTS["welcome"][display_lang], reply_markup=kb)

@dp.callback_query(F.data.startswith("lang:"))
async def on_lang_change(cq: CallbackQuery):
    display_lang = cq.data.split(":")[1]
    if display_lang not in ALL_LANGS:
        display_lang = "en"
    USER_LANG[cq.from_user.id] = display_lang

    bucket = lang_bucket(display_lang)
    invite = await get_invite_link(bucket)
    kb = main_menu_kb(display_lang, invite)

    await cq.message.edit_text(TEXTS["welcome"][display_lang], reply_markup=kb)
    await cq.answer(TEXTS["lang_switched"][display_lang])

@dp.callback_query(F.data == "im_in")
async def on_im_in(cq: CallbackQuery):
    display_lang = USER_LANG.get(cq.from_user.id, "en")
    bucket = lang_bucket(display_lang)
    gid = GROUP.get(bucket, 0)
    if not gid:
        await cq.answer("Group is not configured", show_alert=True)
        return
    try:
        member = await bot.get_chat_member(chat_id=gid, user_id=cq.from_user.id)
        status = getattr(member, "status", None)
        code = get_assigned_code(cq.from_user.id)
        if not code:
            code = assign_code(cq.from_user.id, bucket)
        if status in ("member", "administrator", "creator"):
            if already_sent_any(cq.from_user.id):
                txt = TEXTS["already_sent"][display_lang].replace("{CODE}", code)
            else:
                txt = TEXTS["code_dm"][display_lang].replace("{CODE}", code)
                mark_sent(cq.from_user.id, bucket)
            await bot.send_message(cq.from_user.id, txt, parse_mode="Markdown")
            await cq.answer("✅ Bonus sent in DM")
        else:
            await cq.answer(TEXTS["not_member_yet"][display_lang], show_alert=True)
    except Exception as e:
        print(f"[check member] {e}")
        await cq.answer(TEXTS["not_member_yet"][display_lang], show_alert=True)

@dp.chat_member()
async def on_join(evt: ChatMemberUpdated):
    if evt.new_chat_member.status != "member":
        return

    user = evt.new_chat_member.user
    display_lang = USER_LANG.get(user.id, "en")

    rev = reverse_group_map()
    candidates = rev.get(evt.chat.id, [])
    if len(candidates) == 1:
        bucket = candidates[0]
    else:
        bucket = lang_bucket(display_lang)

    code = get_assigned_code(user.id)
    if not code:
        code = assign_code(user.id, bucket)

    if already_sent_any(user.id):
        txt = TEXTS["already_sent"][display_lang].replace("{CODE}", code)
    else:
        txt = TEXTS["code_dm"][display_lang].replace("{CODE}", code)
        mark_sent(user.id, bucket)

    try:
        await bot.send_message(user.id, txt, parse_mode="Markdown")
    except Exception as e:
        print(f"[dm] failed to {user.id}: {e}")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))