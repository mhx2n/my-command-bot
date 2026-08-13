# ============================================================
# Rich Message engine (Telegram Bot API 10.1 rich markdown)
# ------------------------------------------------------------
# Uses Telethon (MTProto) with the bot token, so the bot can send
# native rich messages: tables, headings, task lists, LaTeX, quotes.
#
# Environment variables (set these on Render):
#   API_ID        -> your Telegram api_id     (integer)
#   API_HASH      -> your Telegram api_hash
#   BOT_TOKEN     -> already used by the bot
#   RICH_FORMAT   -> "0" to disable rich sending completely
#
# If anything is missing or the installed Telethon layer is too old,
# every function degrades silently and the caller falls back to the
# normal HTML message. The bot never crashes because of rich mode.
# ============================================================

from __future__ import annotations

import asyncio
import html as _html
import logging
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger("rich_format")

API_ID_RAW = (os.getenv("API_ID") or os.getenv("TELEGRAM_API_ID") or "").strip()
API_HASH = (os.getenv("API_HASH") or os.getenv("TELEGRAM_API_HASH") or "").strip()
BOT_TOKEN = (os.getenv("BOT_TOKEN") or "").strip()
RICH_ENABLED_ENV = (os.getenv("RICH_FORMAT", "1").strip().lower() not in {"0", "false", "off", "no"})

try:
    API_ID = int(API_ID_RAW) if API_ID_RAW else 0
except Exception:
    API_ID = 0

_TELETHON_OK = False
_RICH_TYPES_OK = False

try:  # pragma: no cover - import guard
    from telethon import TelegramClient, functions, types  # type: ignore
    from telethon.sessions import StringSession  # type: ignore

    _TELETHON_OK = True
    _RICH_TYPES_OK = hasattr(types, "InputRichMessageMarkdown")
except Exception as exc:  # pragma: no cover
    TelegramClient = None  # type: ignore
    functions = None  # type: ignore
    types = None  # type: ignore
    StringSession = None  # type: ignore
    logger.info("Telethon unavailable, rich messages disabled: %s", exc)


_client: Any = None
_client_lock: Optional[asyncio.Lock] = None
_start_failed = False


def rich_configured() -> bool:
    """True when rich sending can even be attempted."""
    return bool(
        RICH_ENABLED_ENV
        and _TELETHON_OK
        and _RICH_TYPES_OK
        and API_ID
        and API_HASH
        and BOT_TOKEN
        and not _start_failed
    )


def rich_status_text() -> str:
    if not RICH_ENABLED_ENV:
        return "Disabled (RICH_FORMAT=0)"
    if not _TELETHON_OK:
        return "Telethon not installed"
    if not _RICH_TYPES_OK:
        return "Telethon too old (no rich message types)"
    if not API_ID or not API_HASH:
        return "API_ID / API_HASH missing"
    if _start_failed:
        return "Login failed (check API_ID / API_HASH)"
    if _client is not None:
        return "Active"
    return "Ready (not connected yet)"


async def _get_client() -> Any:
    global _client, _client_lock, _start_failed
    if not rich_configured():
        return None
    if _client is not None:
        return _client
    if _client_lock is None:
        _client_lock = asyncio.Lock()
    async with _client_lock:
        if _client is not None:
            return _client
        try:
            client = TelegramClient(StringSession(), API_ID, API_HASH)  # type: ignore[misc]
            await client.start(bot_token=BOT_TOKEN)  # type: ignore[union-attr]
            _client = client
            logger.info("Rich message client connected.")
        except Exception as exc:
            _start_failed = True
            logger.warning("Rich message client failed to start: %s", exc)
            return None
    return _client


async def shutdown() -> None:
    global _client
    client = _client
    _client = None
    if client is not None:
        try:
            await client.disconnect()
        except Exception:
            pass


# ------------------------------------------------------------
# Peer + keyboard helpers
# ------------------------------------------------------------

async def _resolve_peer(client: Any, chat_id: int) -> Any:
    try:
        return await client.get_input_entity(chat_id)
    except Exception:
        pass
    try:
        cid = int(chat_id)
    except Exception:
        return None
    if cid >= 0:
        return types.InputPeerUser(user_id=cid, access_hash=0)  # type: ignore[union-attr]
    if str(cid).startswith("-100"):
        return types.InputPeerChannel(channel_id=int(str(cid)[4:]), access_hash=0)  # type: ignore[union-attr]
    return types.InputPeerChat(chat_id=-cid)  # type: ignore[union-attr]


def _convert_markup(reply_markup: Any) -> Any:
    """Convert a python-telegram-bot InlineKeyboardMarkup to a Telethon markup."""
    if reply_markup is None or types is None:
        return None
    rows_src = getattr(reply_markup, "inline_keyboard", None)
    if not rows_src:
        return None
    rows: List[Any] = []
    for row in rows_src:
        buttons: List[Any] = []
        for btn in row:
            text = str(getattr(btn, "text", "") or "")
            url = getattr(btn, "url", None)
            cb = getattr(btn, "callback_data", None)
            if url:
                buttons.append(types.KeyboardButtonUrl(text=text, url=str(url)))
            elif cb is not None:
                data = cb if isinstance(cb, bytes) else str(cb).encode("utf-8")
                buttons.append(types.KeyboardButtonCallback(text=text, data=data))
        if buttons:
            rows.append(types.KeyboardButtonRow(buttons=buttons))
    if not rows:
        return None
    return types.ReplyInlineMarkup(rows=rows)


# ------------------------------------------------------------
# Sending
# ------------------------------------------------------------

async def send_rich(
    chat_id: int,
    markdown: str,
    reply_markup: Any = None,
    plain_fallback: str = "rich message",
    reply_to: Optional[int] = None,
) -> bool:
    """Send a native rich markdown message. Returns True on success."""
    if not markdown or not markdown.strip():
        return False
    client = await _get_client()
    if client is None:
        return False
    try:
        peer = await _resolve_peer(client, chat_id)
        if peer is None:
            return False
        kwargs: Dict[str, Any] = {
            "peer": peer,
            "message": plain_fallback[:200] or "rich message",
            "rich_message": types.InputRichMessageMarkdown(markdown=markdown),  # type: ignore[union-attr]
        }
        if reply_to:
            try:
                kwargs["reply_to"] = types.InputReplyToMessage(reply_to_msg_id=int(reply_to))  # type: ignore[union-attr]
            except Exception:
                pass
        markup = _convert_markup(reply_markup)
        if markup is not None:
            kwargs["reply_markup"] = markup
        try:
            await client(functions.messages.SendMessageRequest(**kwargs))  # type: ignore[union-attr]
        except Exception:
            kwargs.pop("reply_to", None)
            await client(functions.messages.SendMessageRequest(**kwargs))  # type: ignore[union-attr]
        return True
    except Exception as exc:
        logger.info("Rich send failed for %s: %s", chat_id, exc)
        return False



# ------------------------------------------------------------
# Markdown building helpers
# ------------------------------------------------------------

_MD_SPECIALS = r"\\`*_{}[]()#+-.!|<>~="


def md_escape(text: Any) -> str:
    """Escape text so it renders literally inside rich markdown."""
    s = str(text if text is not None else "")
    s = s.replace("\\", "\\\\")
    for ch in "`*_[]()#+-|{}<>~=!":
        s = s.replace(ch, "\\" + ch)
    return s


def md_cell(text: Any, limit: int = 60) -> str:
    """Escape and flatten a value so it is safe inside a markdown table cell."""
    s = str(text if text is not None else "")
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    s = s.replace("\\", "\\\\").replace("|", "\\|")
    for ch in "`*_[]":
        s = s.replace(ch, "\\" + ch)
    return s or "—"


def md_table(
    headers: Sequence[Any],
    rows: Iterable[Sequence[Any]],
    aligns: Optional[Sequence[str]] = None,
    cell_limit: int = 60,
) -> str:
    """Build a rich-markdown table. aligns: 'l' | 'c' | 'r' per column."""
    head = [md_cell(h, cell_limit) for h in headers]
    n = len(head)
    if not aligns or len(aligns) != n:
        aligns = ["l"] * n
    sep = []
    for a in aligns:
        a = (a or "l").lower()[0]
        sep.append(":---:" if a == "c" else ("---:" if a == "r" else ":---"))
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        cells = [md_cell(c, cell_limit) for c in list(row)[:n]]
        while len(cells) < n:
            cells.append("—")
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def md_task_list(items: Iterable[Tuple[bool, Any]]) -> str:
    return "\n".join(f"- [{'x' if done else ' '}] {md_escape(text)}" for done, text in items)


def md_quote(text: Any) -> str:
    return "\n".join(f"> {line}" for line in str(text).splitlines() or [""])


_TAG_RE = re.compile(r"<[^>]+>")


def html_to_markdown(html_text: str) -> str:
    """Convert the bot's simple HTML messages into rich markdown."""
    if not html_text:
        return ""
    s = str(html_text)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?(?:b|strong)>", "**", s, flags=re.I)
    s = re.sub(r"</?(?:i|em)>", "*", s, flags=re.I)
    s = re.sub(r"</?(?:u|ins)>", "", s, flags=re.I)
    s = re.sub(r"</?(?:s|del|strike)>", "~~", s, flags=re.I)
    s = re.sub(r"<pre[^>]*>(.*?)</pre>", lambda m: f"\n```\n{m.group(1)}\n```\n", s, flags=re.I | re.S)
    s = re.sub(r"</?code>", "`", s, flags=re.I)
    s = re.sub(
        r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>',
        lambda m: f"[{m.group(2)}]({m.group(1)})",
        s,
        flags=re.I | re.S,
    )
    s = re.sub(r"<blockquote[^>]*>(.*?)</blockquote>", lambda m: md_quote(m.group(1)), s, flags=re.I | re.S)
    s = _TAG_RE.sub("", s)
    s = _html.unescape(s)
    return s.strip()
