from datetime import datetime
from typing import Callable

import aiormq
import aiormq.types
import msgpack
from common.config import Config
from loguru import logger


def decode_datetime(obj):
    if "__datetime__" in obj:
        obj = datetime.strptime(obj["as_str"], "%Y%m%dT%H:%M:%S.%f")
    return obj


def encode_datetime(obj):
    if isinstance(obj, datetime):
        return {"__datetime__": True, "as_str": obj.strftime("%Y%m%dT%H:%M:%S.%f")}
    return obj


class AsyncRabbitMQQueueManager:
    def __init__(self, uri: str | None = None, exchange: str = "data_exchange"):
        self.uri = uri or Config.get_rabbitmq_uri()
        self.exchange = exchange
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aiormq.connect(self.uri)
        self.channel = await self.connection.channel()
        await self.channel.exchange_declare(
            exchange=self.exchange, exchange_type="topic"
        )

    async def get_channel(self) -> aiormq.types.AbstractChannel:
        """Get or create a channel for the current thread."""
        if not self.channel:
            await self.connect()
        assert self.channel, "Connection not established."
        return self.channel

    async def publish(self, routing_key: str, message: dict) -> None:
        """Publish a message to the specified routing key."""
        channel = await self.get_channel()

        logger.debug(f"Publishing message to '{routing_key}': {message}")
        body: bytes = msgpack.packb(message, default=encode_datetime)
        await channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=body,
        )

    async def consume(self, routing_key: str, callback: Callable) -> None:
        """Consume messages from the specified routing key pattern."""
        channel = await self.get_channel()

        result = await channel.queue_declare("", exclusive=True)
        queue_name = result.queue

        assert queue_name, "Queue name not found."
        logger.info(f"Subscribing to '{routing_key}' with queue '{queue_name}'.")
        await channel.queue_bind(
            exchange=self.exchange, queue=queue_name, routing_key=routing_key
        )

        async def on_message(message: aiormq.types.DeliveredMessage):
            message = msgpack.unpackb(message.body, object_hook=decode_datetime)
            await callback(message)

        await self.channel.basic_consume(queue=queue_name, consumer_callback=on_message)
