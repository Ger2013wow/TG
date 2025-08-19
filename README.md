# Telegram Button Bot — aiogram 3.7+ (Python 3.12 ready)

Бот «досылает» сообщение с кнопкой под каждым постом/сообщением.
Совместим с Railway (Python 3.12): aiogram 3.7+ + aiohttp >= 3.9.

## Переменные окружения
- `BOT_TOKEN` — токен бота.
- `CHAT_IDS` — (опц.) список chat id через запятую. Если пусто — discovery: id появится в логах при первом сообщении.
- `BUTTON_TEXT` — текст кнопки (по умолчанию: «ЛОМАЙ МЕНЯ»).
- `BUTTON_URL`  — ссылка (по умолчанию: https://ya.ru).
- `BUTTON_HEADER_TEXT` — текст сообщения бота (по умолчанию: «👉 Нажми кнопку ниже»).

## Важно
- Для работы в группах отключите Privacy Mode у бота через @BotFather: `/setprivacy → Disable`.
- Добавьте бота участником группы/канала.
- Для каналов бот увидит `channel_post`, хэндлер выше покрывает и это, так как aiogram доставляет его как Message.

## Запуск
```bash
pip install -r requirements.txt
export BOT_TOKEN=xxx
python main.py
```
