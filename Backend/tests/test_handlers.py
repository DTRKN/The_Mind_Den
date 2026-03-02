"""
tests/test_handlers.py
───────────────────────
Юнит-тесты обработчиков бота (без реального Telegram).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers import _split_message, MODE_CHAT, MODE_CODE


# ─── _split_message ───────────────────────────────────────────────────────────

def test_split_message_short():
    parts = _split_message("Короткий текст")
    assert parts == ["Короткий текст"]


def test_split_message_long():
    text = "x" * 9000
    parts = _split_message(text, max_len=4000)
    assert len(parts) == 3
    assert all(len(p) <= 4000 for p in parts)
    assert "".join(parts) == text


def test_split_message_exact():
    text = "x" * 4000
    parts = _split_message(text, max_len=4000)
    assert len(parts) == 1


# ─── whitelist_only ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_whitelist_blocks_unknown_user():
    from bot.handlers import whitelist_only

    @whitelist_only
    async def dummy(update, context):
        return "OK"

    update = MagicMock()
    update.effective_user.id = 99999  # не в whitelist
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("bot.handlers.ALLOWED_USER_IDS", [12345]):
        result = await dummy(update, context)

    update.message.reply_text.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_whitelist_allows_known_user():
    from bot.handlers import whitelist_only

    @whitelist_only
    async def dummy(update, context):
        return "OK"

    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("bot.handlers.ALLOWED_USER_IDS", [12345]):
        result = await dummy(update, context)

    assert result == "OK"


# ─── cmd_start ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmd_start_sets_chat_mode():
    from bot.handlers import cmd_start

    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {}

    with patch("bot.handlers.ALLOWED_USER_IDS", [12345]):
        await cmd_start(update, context)

    assert context.user_data.get("mode") == MODE_CHAT
    update.message.reply_text.assert_called_once()
