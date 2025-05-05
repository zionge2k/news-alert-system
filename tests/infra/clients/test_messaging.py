"""
Tests for messaging client implementation.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

# Add project root to path to support imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infra.clients.messaging import DiscordClient, Message, MessagingClient


class TestMessage(unittest.TestCase):
    """Test case for Message model."""

    def test_create_message(self):
        """Test creating a message."""
        # Create a message
        message = Message(
            content="Test content",
            title="Test Title",
            url="https://example.com",
            color="#ff0000",
            fields=[{"name": "Field", "value": "Value"}],
            footer="Test footer",
            thumbnail_url="https://example.com/thumb.jpg",
            image_url="https://example.com/image.jpg",
        )

        # Assertions
        self.assertEqual(message.content, "Test content")
        self.assertEqual(message.title, "Test Title")
        self.assertEqual(message.url, "https://example.com")
        self.assertEqual(message.color, "#ff0000")
        self.assertEqual(message.fields, [{"name": "Field", "value": "Value"}])
        self.assertEqual(message.footer, "Test footer")
        self.assertEqual(message.thumbnail_url, "https://example.com/thumb.jpg")
        self.assertEqual(message.image_url, "https://example.com/image.jpg")

    def test_create_minimal_message(self):
        """Test creating a message with minimal fields."""
        # Create a message with only required fields
        message = Message(content="Test content")

        # Assertions
        self.assertEqual(message.content, "Test content")
        self.assertIsNone(message.title)
        self.assertIsNone(message.url)
        self.assertIsNone(message.color)
        self.assertIsNone(message.fields)
        self.assertIsNone(message.footer)
        self.assertIsNone(message.thumbnail_url)
        self.assertIsNone(message.image_url)


class TestDiscordClient(unittest.TestCase):
    """Test case for Discord client implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Patch the discord.Client to avoid actual connections
        self.client_patcher = patch("discord.Client")
        self.mock_discord_client = self.client_patcher.start()

        # Set up mock intents
        self.intents_patcher = patch("discord.Intents.default")
        self.mock_intents = self.intents_patcher.start()

        # Create client
        self.discord_client = DiscordClient(
            token="test-token",
            guild_id="test-guild",
            default_channel_id="default-channel",
            max_retries=2,
            retry_delay=1,
        )

        # Get the internal discord client
        self.internal_client = self.discord_client._client

    def tearDown(self):
        """Tear down test fixtures."""
        self.client_patcher.stop()
        self.intents_patcher.stop()

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test connecting to Discord."""
        # Mock the client's start method
        self.internal_client.start = AsyncMock()
        self.internal_client.is_ready = MagicMock(return_value=True)

        # Call the method
        await self.discord_client.connect()

        # Assertions
        self.internal_client.start.assert_called_once_with("test-token")

    @pytest.mark.asyncio
    async def test_connect_retry(self):
        """Test connection retry."""
        # Mock the client's start method to fail first
        self.internal_client.start = AsyncMock(
            side_effect=[Exception("Connection error"), None]
        )
        # Mock is_ready to return False first, then True
        self.internal_client.is_ready = MagicMock(side_effect=[False, True])

        # Patch asyncio.sleep to avoid delays
        with patch("asyncio.sleep", AsyncMock()):
            # Call the method
            await self.discord_client.connect()

        # Assertions
        self.assertEqual(self.internal_client.start.call_count, 2)

    @pytest.mark.asyncio
    async def test_connect_max_retries(self):
        """Test connection max retries."""
        # Mock the client's start method to always fail
        self.internal_client.start = AsyncMock(
            side_effect=Exception("Connection error")
        )

        # Patch asyncio.sleep to avoid delays
        with patch("asyncio.sleep", AsyncMock()):
            # Call the method - should raise ConnectionError
            with self.assertRaises(ConnectionError):
                await self.discord_client.connect()

        # Assertions
        self.assertEqual(self.internal_client.start.call_count, 2)  # max_retries=2

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnecting from Discord."""
        # Mock the client's close method
        self.internal_client.close = AsyncMock()

        # Call the method
        await self.discord_client.disconnect()

        # Assertions
        self.internal_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_channel(self):
        """Test getting a Discord channel."""
        # Mock client methods
        self.internal_client.is_ready = MagicMock(return_value=True)
        self.internal_client.get_channel = MagicMock(return_value="test-channel")

        # Call the method
        channel = await self.discord_client._get_channel("123456")

        # Assertions
        self.internal_client.get_channel.assert_called_once_with(123456)
        self.assertEqual(channel, "test-channel")

    @pytest.mark.asyncio
    async def test_get_channel_fetch(self):
        """Test fetching a Discord channel when get_channel returns None."""
        # Mock client methods
        self.internal_client.is_ready = MagicMock(return_value=True)
        self.internal_client.get_channel = MagicMock(return_value=None)
        self.internal_client.fetch_channel = AsyncMock(return_value="fetched-channel")

        # Call the method
        channel = await self.discord_client._get_channel("123456")

        # Assertions
        self.internal_client.get_channel.assert_called_once_with(123456)
        self.internal_client.fetch_channel.assert_called_once_with(123456)
        self.assertEqual(channel, "fetched-channel")

    @pytest.mark.asyncio
    async def test_get_channel_not_ready(self):
        """Test getting a channel when client is not ready."""
        # Mock client method
        self.internal_client.is_ready = MagicMock(return_value=False)

        # Call the method - should raise ValueError
        with self.assertRaises(ValueError):
            await self.discord_client._get_channel("123456")

    @pytest.mark.asyncio
    async def test_publish(self):
        """Test publishing a message."""
        # Create a message
        message = Message(
            content="Test content",
            title="Test Title",
            url="https://example.com",
            color="#ff0000",
            fields=[{"name": "Field", "value": "Value"}],
            footer="Test footer",
            thumbnail_url="https://example.com/thumb.jpg",
            image_url="https://example.com/image.jpg",
        )

        # Mock channel and message
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        mock_discord_message = MagicMock()
        mock_discord_message.id = 12345
        mock_channel.send.return_value = mock_discord_message

        # Mock _get_channel method
        self.discord_client._get_channel = AsyncMock(return_value=mock_channel)

        # Call the method
        result = await self.discord_client.publish("channel-id", message)

        # Assertions
        self.discord_client._get_channel.assert_called_once_with("channel-id")
        mock_channel.send.assert_called_once()
        # Assert embed argument was passed
        args, kwargs = mock_channel.send.call_args
        self.assertIn("embed", kwargs)
        self.assertEqual(result, "12345")

    @pytest.mark.asyncio
    async def test_publish_default_channel(self):
        """Test publishing a message to the default channel."""
        # Create a message
        message = Message(content="Test content")

        # Mock channel and message
        mock_channel = MagicMock()
        mock_channel.send = AsyncMock()
        mock_discord_message = MagicMock()
        mock_discord_message.id = 12345
        mock_channel.send.return_value = mock_discord_message

        # Mock _get_channel method
        self.discord_client._get_channel = AsyncMock(return_value=mock_channel)

        # Call the method with None channel
        result = await self.discord_client.publish(None, message)

        # Assertions
        self.discord_client._get_channel.assert_called_once_with("default-channel")
        mock_channel.send.assert_called_once()
        self.assertEqual(result, "12345")

    @pytest.mark.asyncio
    async def test_publish_no_channel(self):
        """Test publishing a message with no channel specified and no default."""
        # Create a message
        message = Message(content="Test content")

        # Set client's default_channel_id to None
        self.discord_client.default_channel_id = None

        # Call the method - should raise ValueError
        with self.assertRaises(ValueError):
            await self.discord_client.publish(None, message)

    @pytest.mark.asyncio
    async def test_subscribe(self):
        """Test subscribing to a channel."""
        # Mock _get_channel method
        self.discord_client._get_channel = AsyncMock()

        # Mock callback
        callback = AsyncMock()

        # Call the method
        await self.discord_client.subscribe("channel-id", callback)

        # Assertions
        self.discord_client._get_channel.assert_called_once_with("channel-id")
        self.assertIn("channel-id", self.discord_client._subscriptions)
        self.assertEqual(self.discord_client._subscriptions["channel-id"], callback)

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from a channel."""
        # Add a subscription
        self.discord_client._subscriptions["channel-id"] = AsyncMock()

        # Call the method
        await self.discord_client.unsubscribe("channel-id")

        # Assertions
        self.assertNotIn("channel-id", self.discord_client._subscriptions)

    @pytest.mark.asyncio
    async def test_unsubscribe_not_subscribed(self):
        """Test unsubscribing from a channel that is not subscribed."""
        # Ensure no subscription
        self.discord_client._subscriptions = {}

        # Call the method - should not raise
        await self.discord_client.unsubscribe("channel-id")

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using the client as a context manager."""
        # Mock methods
        self.discord_client.connect = AsyncMock()
        self.discord_client.disconnect = AsyncMock()

        # Use as context manager
        async with self.discord_client:
            pass

        # Assertions
        self.discord_client.connect.assert_called_once()
        self.discord_client.disconnect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
