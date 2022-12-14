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

# Environment variable keys.
USER_SESSION_KEY = "USER_SESSION_KEY"
BOT_SESSION_KEY = "BOT_SESSION_KEY"
API_ID = "API_ID"
API_HASH = "API_HASH"

# Telegram channel usernames.
DEFILLAMA = "defillama_tg"
DEFILLAMA_DEV = "defillama_roundup_dev"

# Excerpt content.
TARGET_TOPICS = set(["MEV⚡️", "Development⚙️", "Security🛡"])
TITLE = "**🦙 Excerpt from [DefiLlama Round Up](https://t.me/defillama_tg)**"


class Logger:
    """Log helper."""

    def __init__(self):
        pass

    def log(self, severity: str, message: str):
        """Log helper."""
        print(json.dumps({"severity": severity.upper(), "message": message}))

    def info(self, message: str):
        """Log info."""
        self.log("info", message)

    def warn(self, message: str):
        """Log warning."""
        self.log("warn", message)

    def error(self, message: str):
        """Log error."""
        self.log("error", message)


class Bot:
    """Excerpt bot."""

    def __init__(self):
        self.logger = Logger()
        self.user_session_key = self.get_env(USER_SESSION_KEY)
        self.bot_session_key = self.get_env(BOT_SESSION_KEY)
        self.api_id = int(self.get_env(API_ID))
        self.api_hash = self.get_env(API_HASH)

    async def run(self):
        """Execute bot."""
        messages = await self.collect_messages()
        topics = self.extract_topics(messages)
        content = "\n\n".join([m.message.strip() for m in messages[::-1]]).strip()
        excerpt = self.construct_excerpt(content, topics)
        await self.send_excerpt(excerpt)

    def get_env(self, key: str) -> str:
        """Get environment variables."""
        val = os.getenv(key)
        if val is None:
            self.logger.error(f"Environment variable `{key}` is not set.")
            sys.exit()

        return val

    async def collect_messages(self) -> List[Message]:
        """Collect news messages."""
        async with TelegramClient(
            StringSession(self.user_session_key), self.api_id, self.api_hash
        ) as client:
            # Collect messages that are
            # 1. less than one day old, and
            # 2. not one-off (i.e. contain multiple news items).
            now = datetime.now(dt.timezone.utc)
            messages = [
                m
                async for m in client.iter_messages(DEFILLAMA, limit=8)
                if (now - m.date).days == 0
                and len([e for e in m.entities if isinstance(e, MessageEntityUrl)]) > 1
            ]
            self.logger.info(f"Found {len(messages)} message(s).")

            return messages

    def extract_topics(self, messages: List[Message]) -> Set[str]:
        """Extract section topics."""
        topics = set()
        for message in messages:
            if message.entities is None:
                continue

            bold_entities = []
            for entity in message.entities:
                if isinstance(entity, MessageEntityBold):
                    # Only the text part of the topic will be bold, not the emojis, e.g.
                    # "**MEV**⚡". So we extend the entity to also include the emoji by increasing
                    # the length by 2.
                    entity.length += 2
                    bold_entities.append(entity)

            topics.update([t.strip() for t in get_inner_text(message.message, bold_entities)])

        return topics

    def construct_excerpt(self, content: str, topics: Set[str]) -> str:
        """Construct excerpt from topics of interests."""
        current_topic = ""
        excerpts = []
        for line in content.split("\n\n"):
            if line in topics:
                current_topic = line
            if current_topic in TARGET_TOPICS:
                if line in topics:
                    line = f"**{line}**"
                excerpts.append(line)

        excerpt = "\n\n".join(excerpts)
        if excerpt == "":
            self.logger.warn("Excerpt is empty")
        else:
            excerpt = f"{TITLE}\n\n{excerpt}"
            self.logger.info(f"Excerpt: {excerpt}")

        return excerpt

    async def send_excerpt(self, excerpt: str):
        """Send excerpt to channel."""
        # Skip sending if excerpt is empty.
        if not excerpt:
            return

        async with TelegramClient(
            StringSession(self.bot_session_key), self.api_id, self.api_hash
        ) as client:
            await client.send_message(DEFILLAMA_DEV, excerpt, link_preview=False)


@functions_framework.cloud_event
def handler(event):
    """Handle Pub/Sub event."""
    if not event.data["message"]["attributes"].get("alpaca"):
        return

    bot = Bot()
    asyncio.run(bot.run())
