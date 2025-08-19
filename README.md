# Telegram Button Bot (Railway-ready)

Этот бот автоматически добавляет кнопку «ЛОМАЙ МЕНЯ» (https://ya.ru) под любым постом в чате/канале.

## Почему прошлый билд упал на Railway
Railway использует Python 3.12. Старые версии `aiohttp` (<3.9) не совместимы с Python 3.12 и пытаются собраться из исходников, что падает с ошибкой `PyLongObject ... ob_digit`.
Фикс: явно закрепить `aiohttp>=3.9.5,<4.0.0` — есть готовые колёса для cp312.

## Запуск локально
```bash
pip install -r requirements.txt
export BOT_TOKEN=ваш_токен
python main.py
```

## Деплой на Railway
1. Залейте эти файлы.
2. В Variables добавьте `BOT_TOKEN` со значением токена бота.
3. Railway прочитает Procfile и запустит процесс `worker: python main.py`.

### Альтернативный обходной путь (если всё ещё беда со сборкой)
- Установить переменную окружения `PYTHON_VERSION=3.11.9` в Railway (Settings → Variables) — это переведёт проект на Python 3.11, где и старые aiohttp работают.
- Но основной рекомендуемый путь — оставить Python 3.12 и использовать aiohttp >= 3.9.5.
