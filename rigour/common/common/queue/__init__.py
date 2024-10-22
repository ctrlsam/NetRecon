from abc import ABC, abstractmethod


class QueueManagerInterface(ABC):
    @abstractmethod
    def connect(self):
        """Establish connection to the message broker."""

    @abstractmethod
    def publish(self, routing_key: str, message: dict):
        """Publish a message to a specific routing key."""

    @abstractmethod
    def consume(self, routing_key: str, callback):
        """Consume messages from a specific routing key."""

    @abstractmethod
    def close(self):
        """Close the connection to the message broker."""
