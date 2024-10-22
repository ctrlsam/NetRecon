import json
import threading
from typing import Callable

import pika
from common.config import Config
from common.utils import DateTimeEncoder
from loguru import logger

from . import QueueManagerInterface


class RabbitMQQueueManager(QueueManagerInterface):
    def __init__(self, uri: str | None = None, exchange="data_exchange"):
        self.uri = uri or Config.get_rabbitmq_uri()
        self.exchange = exchange

        # Create a thread-local storage for the connection and channel
        # This prevents thread errors when using the same connection in multiple threads
        self.local = threading.local()

    def connect(self):
        self.local.connection = pika.BlockingConnection(pika.URLParameters(self.uri))
        self.local.channel = self.local.connection.channel()
        self.local.channel.exchange_declare(
            exchange=self.exchange, exchange_type="topic"
        )
        logger.info(
            f"Thread {threading.current_thread().name}: Connected to RabbitMQ on\
                {self.uri}, exchange '{self.exchange}' declared."
        )

    def _get_channel(self):
        """Get or create a channel for the current thread."""
        if not hasattr(self.local, "channel"):
            self.connect()
        return self.local.channel

    def publish(self, routing_key: str, message: dict):
        """Publish a message to the specified routing key."""
        channel = self._get_channel()
        channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=json.dumps(message, cls=DateTimeEncoder),
        )
        logger.debug(f"Published message to '{routing_key}': {message}")

    def consume(self, routing_key: str, callback: Callable):
        """Consume messages from the specified routing key pattern."""
        channel = self._get_channel()
        result = channel.queue_declare("", exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(
            exchange=self.exchange, queue=queue_name, routing_key=routing_key
        )
        logger.info(f"Subscribed to '{routing_key}' with queue '{queue_name}'.")

        def on_message(channel, method, properties, body):
            message = json.loads(body)
            logger.debug(f"Received message from '{method.routing_key}': {message}")
            callback(message)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=queue_name, on_message_callback=on_message)
        logger.info("Starting consumption...")
        try:
            channel.start_consuming()
        except Exception as e:
            logger.exception(f"Error consuming messages: {e}")
            self.close()

    def close(self):
        """Close the connection to the RabbitMQ server."""
        if hasattr(self.local, "connection") and not self.local.connection.is_closed:
            self.local.connection.close()
            logger.info("Connection to RabbitMQ closed.")
