"""Alpaca Excerpt Bot."""
import asyncio
import datetime as dt
import json
import os
import sys
from datetime import datetime
from typing import List, Set

import functions_framework
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.types import Message, MessageEntityBold, MessageEntityUrl
from telethon.utils import get_inner_text


def log(severity: str, message: str):
    """Log helper."""
    print(json.dumps({"severity": severity.upper(), "message": message}))


def get_env(key: str) -> str:
    """Get environment variable."""
    val = os.getenv(key)
    if val is None:
        log("err", f"Environment variable `{key}` is not set.")
        sys.exit()
    return val


async def collect_messages(session_key: str, api_id: int, api_hash: str) -> List[Message]:
    """Collect news messages."""
    async with TelegramClient(StringSession(session_key), api_id, api_hash) as client:
        # Collect messages that are
        # 1. less than one day old, and
        # 2. not one-off (i.e. contain multiple news items).
        now = datetime.now(dt.timezone.utc)
        messages = [
            m
            async for m in client.iter_messages("defillama_tg", limit=8)
            if (now - m.date).days == 0
            and len([e for e in m.entities if isinstance(e, MessageEntityUrl)]) > 1
        ]
        log("info", f"Found {len(messages)} messages.")

        return messages


def extract_topics(messages: List[Message]) -> Set[str]:
    """Extract section topics."""
    topics = set()
    for message in messages:
        if message.entities is None:
            continue

        bold_entities = []
        for entity in message.entities:
            if isinstance(entity, MessageEntityBold):
                # Only the text part of the topic will be bold, not the emojis, e.g. "**MEV**⚡". So
                # we extend the entity to also include the emoji by increasing the length by 2.
                entity.length += 2
                bold_entities.append(entity)

        topics.update([t.strip() for t in get_inner_text(message.message, bold_entities)])

    return topics


def construct_excerpt(content: str, topics: Set[str]) -> str:
    """Construct excerpt from topics of interests."""
    target_topics = set(["MEV⚡️", "Development⚙️", "Security🛡"])
    current_topic = ""
    excerpts = []
    for line in content.split("\n\n"):
        if line in topics:
            current_topic = line
        if current_topic in target_topics:
            if line in topics:
                line = f"**{line}**"
            excerpts.append(line)

    title = "**🦙 Excerpt from [DefiLlama Round Up](https://t.me/defillama_tg)**"
    excerpt = "\n\n".join(excerpts)
    excerpt = f"{title}\n\n{excerpt}" if excerpts else ""
    log("info" if excerpt else "warn", f"Excerpt content: {excerpt}")

    return excerpt


async def send_excerpt(session_key: str, api_id: int, api_hash: str, excerpt: str):
    """Send excerpt to channel."""
    # Skip sending if excerpt is empty.
    if not excerpt:
        return

    async with TelegramClient(StringSession(session_key), api_id, api_hash) as client:
        await client.send_message("defillama_roundup_dev", excerpt, link_preview=False)


async def main():
    """Handle logic."""
    user_session_key = get_env("USER_SESSION_KEY")
    bot_session_key = get_env("BOT_SESSION_KEY")
    api_id = int(get_env("API_ID"))
    api_hash = get_env("API_HASH")

    messages = await collect_messages(user_session_key, api_id, api_hash)
    topics = extract_topics(messages)
    content = "\n\n".join([m.message for m in messages[::-1]]).strip()
    excerpt = construct_excerpt(content, topics)
    await send_excerpt(bot_session_key, api_id, api_hash, excerpt)


@functions_framework.cloud_event
def handler(event):
    """Handle Pub/Sub event."""
    if not event["data"]["message"]["attributes"].get("alpaca"):
        return

    asyncio.run(main())
