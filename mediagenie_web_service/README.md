# MediaGenieBot 🎬🎧

Мультимедийный Telegram-бот, который умеет:

- 🎵 Искать и отправлять музыку с YouTube `/music <название>`
- 🎬 Искать фильмы с описанием и рейтингом IMDb `/movie <название>`
- 🎌 Искать аниме через MyAnimeList `/anime <название>`

## 🚀 Деплой на Render (Web Service)

### 📦 Что внутри

- `main.py` — основной код бота
- `requirements.txt` — зависимости
- `README.md` — описание

### 🔧 Как развернуть на Render

1. Залей проект на GitHub
2. Перейди на [render.com](https://render.com)
3. Создай **New Web Service**
4. Укажи:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
5. В разделе **Environment** добавь переменные:
   ```
   BOT_TOKEN = <твой токен Telegram-бота>
   OMDB_API_KEY = 73603e14
   ```

### ✅ Пример команд в Telegram

- `/start` — главное меню
- `/music Believer` — найти музыку
- `/movie Inception` — найти фильм
- `/anime Death Note` — найти аниме

---

## 📄 Лицензия

MIT License
