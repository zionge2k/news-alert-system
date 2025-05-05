"""
Messaging client interface and implementations.

This module provides interfaces and implementations for various messaging systems
like Discord, Telegram, etc. for pub/sub operations and notifications.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import discord
from discord.ext import tasks
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Base message model for messaging clients."""

    content: str = Field(..., description="The message content")
    title: Optional[str] = Field(None, description="Optional message title")
    url: Optional[str] = Field(None, description="Optional URL related to the message")
    color: Optional[str] = Field(
        None, description="Optional color for the message (e.g. hex code)"
    )
    fields: Optional[List[Dict[str, str]]] = Field(
        None, description="Optional list of field name-value pairs"
    )
    footer: Optional[str] = Field(None, description="Optional footer text")
    thumbnail_url: Optional[str] = Field(None, description="Optional thumbnail URL")
    image_url: Optional[str] = Field(None, description="Optional image URL")


class MessagingClient(ABC):
    """Interface for messaging clients."""

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the messaging service.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Disconnect from the messaging service.

        Raises:
            ConnectionError: If disconnection fails
        """
        pass

    @abstractmethod
    async def publish(self, channel: str, message: Message) -> str:
        """
        Publish a message to a channel.

        Args:
            channel: The channel to publish to
            message: The message to publish

        Returns:
            A message ID or reference

        Raises:
            Exception: If publishing fails
        """
        pass

    @abstractmethod
    async def subscribe(self, channel: str, callback: callable) -> None:
        """
        Subscribe to a channel to receive messages.

        Args:
            channel: The channel to subscribe to
            callback: The callback function to invoke when a message is received

        Raises:
            Exception: If subscription fails
        """
        pass

    @abstractmethod
    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.

        Args:
            channel: The channel to unsubscribe from

        Raises:
            Exception: If unsubscription fails
        """
        pass


class DiscordClient(MessagingClient):
    """Discord implementation of messaging client."""

    def __init__(
        self,
        token: str,
        guild_id: Optional[str] = None,
        default_channel_id: Optional[str] = None,
        reconnect: bool = True,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """
        Initialize the Discord client.

        Args:
            token: Discord bot token
            guild_id: Optional Discord server (guild) ID
            default_channel_id: Optional default channel ID
            reconnect: Whether to automatically reconnect if disconnected
            max_retries: Maximum number of connection retries
            retry_delay: Delay between connection retries in seconds
        """
        self.token = token
        self.guild_id = guild_id
        self.default_channel_id = default_channel_id
        self.reconnect = reconnect
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Discord client with intents
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents, reconnect=reconnect)

        # Subscription callbacks
        self._subscriptions = {}

        # Event handlers
        @self._client.event
        async def on_ready():
            logger.info(f"Discord client logged in as {self._client.user}")

        @self._client.event
        async def on_message(message):
            if message.author == self._client.user:
                return  # Ignore own messages

            # Check if we have a subscription for this channel
            channel_id = str(message.channel.id)
            if channel_id in self._subscriptions:
                callback = self._subscriptions[channel_id]

                # Create a Message object
                try:
                    msg = Message(
                        content=message.content,
                        title=f"Message from {message.author}",
                        url=message.jump_url,
                    )

                    # Invoke the callback
                    asyncio.create_task(callback(msg))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    async def connect(self) -> None:
        """
        Connect to Discord.

        Raises:
            ConnectionError: If connection fails after max retries
        """
        for attempt in range(self.max_retries):
            try:
                # Discord client's run() is blocking, so use start() and wait for connection
                asyncio.create_task(self._client.start(self.token))

                # Wait for client to be ready
                ready_timeout = 30  # seconds
                start_time = asyncio.get_event_loop().time()
                while not self._client.is_ready():
                    await asyncio.sleep(0.1)
                    if asyncio.get_event_loop().time() - start_time > ready_timeout:
                        raise TimeoutError(
                            "Timed out waiting for Discord client to connect"
                        )

                logger.info("Connected to Discord")
                return
            except Exception as e:
                logger.warning(
                    f"Discord connection failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Discord connection failed after {self.max_retries} attempts"
                    )
                    raise ConnectionError(f"Failed to connect to Discord: {e}")

    async def disconnect(self) -> None:
        """
        Disconnect from Discord.

        Raises:
            ConnectionError: If disconnection fails
        """
        try:
            if self._client:
                await self._client.close()
                logger.info("Disconnected from Discord")
        except Exception as e:
            logger.error(f"Error disconnecting from Discord: {e}")
            raise ConnectionError(f"Failed to disconnect from Discord: {e}")

    async def _get_channel(self, channel_id: str) -> discord.TextChannel:
        """
        Get a Discord channel by ID.

        Args:
            channel_id: The channel ID

        Returns:
            The Discord channel

        Raises:
            ValueError: If the channel cannot be found
        """
        if not self._client.is_ready():
            raise ValueError("Discord client is not connected")

        try:
            channel = self._client.get_channel(int(channel_id))
            if channel is None:
                # Try fetching the channel
                channel = await self._client.fetch_channel(int(channel_id))

            if channel is None:
                raise ValueError(f"Channel {channel_id} not found")

            return channel
        except Exception as e:
            logger.error(f"Error getting Discord channel: {e}")
            raise ValueError(f"Error getting Discord channel: {e}")

    async def publish(self, channel: str, message: Message) -> str:
        """
        Publish a message to a Discord channel.

        Args:
            channel: The channel ID to publish to, or None to use default
            message: The message to publish

        Returns:
            The Discord message ID

        Raises:
            Exception: If publishing fails
        """
        try:
            channel_id = channel or self.default_channel_id
            if not channel_id:
                raise ValueError("No channel ID provided and no default channel ID set")

            discord_channel = await self._get_channel(channel_id)

            # Create a Discord embed
            embed = discord.Embed(
                title=message.title,
                description=message.content,
                url=message.url,
                color=(
                    discord.Color.from_str(message.color)
                    if message.color
                    else discord.Color.blue()
                ),
            )

            if message.thumbnail_url:
                embed.set_thumbnail(url=message.thumbnail_url)

            if message.image_url:
                embed.set_image(url=message.image_url)

            if message.footer:
                embed.set_footer(text=message.footer)

            if message.fields:
                for field in message.fields:
                    embed.add_field(
                        name=field.get("name", ""),
                        value=field.get("value", ""),
                        inline=field.get("inline", False),
                    )

            # Send the message
            discord_message = await discord_channel.send(embed=embed)
            return str(discord_message.id)
        except Exception as e:
            logger.error(f"Error publishing message to Discord: {e}")
            raise Exception(f"Failed to publish message to Discord: {e}")

    async def subscribe(self, channel: str, callback: callable) -> None:
        """
        Subscribe to a Discord channel.

        Args:
            channel: The channel ID to subscribe to
            callback: The callback function to invoke when a message is received

        Raises:
            Exception: If subscription fails
        """
        try:
            # Validate the channel exists
            await self._get_channel(channel)

            # Register the callback
            self._subscriptions[channel] = callback
            logger.info(f"Subscribed to Discord channel {channel}")
        except Exception as e:
            logger.error(f"Error subscribing to Discord channel: {e}")
            raise Exception(f"Failed to subscribe to Discord channel: {e}")

    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a Discord channel.

        Args:
            channel: The channel ID to unsubscribe from

        Raises:
            Exception: If unsubscription fails
        """
        try:
            if channel in self._subscriptions:
                del self._subscriptions[channel]
                logger.info(f"Unsubscribed from Discord channel {channel}")
            else:
                logger.warning(f"Not subscribed to Discord channel {channel}")
        except Exception as e:
            logger.error(f"Error unsubscribing from Discord channel: {e}")
            raise Exception(f"Failed to unsubscribe from Discord channel: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
