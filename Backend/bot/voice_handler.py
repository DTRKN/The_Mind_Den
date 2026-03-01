"""
voice_handler.py
────────────────
Голосовые сообщения → текст через Groq Whisper.
После транскрипции текст обрабатывается как обычное текстовое сообщение
(может быть напоминанием, code-запросом или AI-чатом).
"""

import os
import tempfile

from groq import AsyncGroq
from telegram import Update, Message
from telegram.ext import ContextTypes

from config import GROQ_API_KEY

groq_client = AsyncGroq(api_key=GROQ_API_KEY)


async def transcribe_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """
    Скачивает голосовое сообщение или аудиофайл,
    отправляет в Groq Whisper и возвращает текст.
    """
    message: Message = update.message

    # Получаем файл (voice или audio)
    if message.voice:
        file_obj = await message.voice.get_file()
        suffix = ".ogg"
    elif message.audio:
        file_obj = await message.audio.get_file()
        suffix = ".mp3"
    else:
        return None

    await message.reply_text("🎙 Распознаю речь...")

    # Скачиваем во временный файл
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await file_obj.download_to_drive(tmp_path)

        with open(tmp_path, "rb") as audio_file:
            transcription = await groq_client.audio.transcriptions.create(
                file=(os.path.basename(tmp_path), audio_file),
                model="whisper-large-v3-turbo",
                language="ru",
                response_format="text",
            )

        return transcription.strip() if transcription else None

    except Exception as e:
        await message.reply_text(f"❌ Ошибка транскрипции: {e}")
        return None

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
