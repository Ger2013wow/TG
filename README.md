# Telegram Button Bot — aiogram 3 (Python 3.12 ready)

Этот бот «досылает» сообщение с кнопкой под каждым постом/сообщением.
Совместим с Railway (Python 3.12) благодаря aiogram 3 + aiohttp>=3.9.

## Переменные окружения
- `BOT_TOKEN` — токен бота.
- `CHAT_IDS` — (опц.) список chat id через запятую. Если пусто — бот в discovery-режиме и пишет id в логи при первом сообщении.
- `BUTTON_TEXT` — текст кнопки (по умолчанию: «ЛОМАЙ МЕНЯ»).
- `BUTTON_URL`  — ссылка кнопки (по умолчанию: https://ya.ru).
- `BUTTON_HEADER_TEXT` — текст сообщения бота (по умолчанию: «👉 Нажми кнопку ниже»).
- `BUTTON_ROW_WIDTH` — ширина ряда (сейчас не используется, одна кнопка на строку).

## Запуск локально
```bash
pip install -r requirements.txt
export BOT_TOKEN=xxx
python main.py
```

## Деплой на Railway
1) Залейте файлы.
2) В Settings → Variables добавьте `BOT_TOKEN` и, при необходимости, `CHAT_IDS` (например: `-1001234567890`).
3) Запустите деплой — Railway прочитает Procfile (`worker: python main.py`).

### Альтернатива
Если хотите остаться на aiogram 2.x — выставьте переменную `PYTHON_VERSION=3.11.9` в Railway и используйте зависимости:
```
aiogram==2.25.1
aiohttp>=3.8,<3.9
```
Но рекомендован текущий вариант (aiogram 3) под Python 3.12.
