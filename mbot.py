import logging
import os
import requests
import aiohttp
import yt_dlp

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from aiohttp import web

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "73603e14")
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO)


# 🔁 Перевод текста
def translate_to_en(text):
    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text},
            timeout=5
        )
        return response.json()[0][0][0]
    except Exception as e:
        logging.error(f"Ошибка перевода: {e}")
        return text


# 🎵 Загрузка музыки
def download_audio(query):
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)['entries'][0]
            title = info['title']
            path = os.path.join(output_dir, f"{title}.mp3")
            return path if os.path.exists(path) else None
    except Exception as e:
        logging.error(f"Ошибка загрузки: {e}")
        return None


# 🎧 Музыка
async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🎵 Введите название песни:\n/music название")
        return
    await update.message.reply_text("⏳ Загружаю музыку...")
    file_path = download_audio(query)
    if file_path:
        with open(file_path, "rb") as audio:
            await update.message.reply_audio(audio)
        os.remove(file_path)
    else:
        await update.message.reply_text("❌ Не удалось загрузить.")


# 🎬 Фильмы
def get_movie_info(title):
    try:
        title_en = translate_to_en(title)
        res = requests.get("http://www.omdbapi.com/", params={
            "t": title_en, "apikey": OMDB_API_KEY, "plot": "short"
        })
        data = res.json()
        if data.get("Response") == "True":
            return (
                f"🎬 *{data['Title']}* ({data['Year']})\n"
                f"⭐ IMDb: {data.get('imdbRating')}\n"
                f"📖 {data.get('Plot')}\n"
                f"[IMDb](https://www.imdb.com/title/{data['imdbID']})",
                data.get("Poster")
            )
    except Exception as e:
        logging.error(f"OMDb ошибка: {e}")
    return None, None


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🎬 Введите название фильма:\n/movie название")
        return
    await update.message.reply_text("🔍 Ищу фильм...")
    info, poster = get_movie_info(query)
    if info:
        if poster and poster != "N/A":
            await update.message.reply_photo(poster, caption=info, parse_mode="Markdown")
        else:
            await update.message.reply_text(info, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Фильм не найден.")


# 🎌 Аниме
async def get_anime_info(title):
    title_en = translate_to_en(title)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.jikan.moe/v4/anime?q={title_en}&limit=1") as r:
                data = await r.json()
                if data.get("data"):
                    anime = data["data"][0]
                    return (
                        f"🎌 *{anime['title']}*\n"
                        f"⭐ {anime.get('score')}\n"
                        f"📖 {anime.get('synopsis')}\n"
                        f"[MyAnimeList]({anime['url']})",
                        anime["images"]["jpg"]["image_url"]
                    )
    except Exception as e:
        logging.error(f"Jikan ошибка: {e}")
    return None, None


async def anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("🎌 Введите название аниме:\n/anime название")
        return
    await update.message.reply_text("🔍 Ищу аниме...")
    info, image = await get_anime_info(query)
    if info:
        if image:
            await update.message.reply_photo(photo=image, caption=info, parse_mode="Markdown")
        else:
            await update.message.reply_text(info, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Аниме не найдено.")


# 👋 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я мультимедийный бот:\n"
        "/music <песня>\n/movie <фильм>\n/anime <аниме>",
        reply_markup=ReplyKeyboardMarkup([['🎵 Музыка']], resize_keyboard=True)
    )


# 🔘 Кнопка "Музыка"
async def handle_music_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Напиши /music <название>")


# 🌐 HTTP-сервер
async def index(request):
    return web.Response(text="✅ MediaGenie работает!")


# 🚀 Старт
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("movie", movie))
    app.add_handler(CommandHandler("anime", anime))
    app.add_handler(MessageHandler(filters.Regex("🎵 Музыка"), handle_music_button))

    # aiohttp сервер для Render
    web_app = web.Application()
    web_app.router.add_get("/", index)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info(f"✅ Web-сервер запущен на порту {PORT}")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
