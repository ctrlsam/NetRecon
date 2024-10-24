import asyncio
import os
from dataclasses import asdict
from datetime import datetime, timedelta

from common import utils
from common.database.mongodb import Database
from common.queue.rabbitmq_asyncio import AsyncRabbitMQQueueManager
from common.types import Banner, HostMessage
from dacite import from_dict
from loguru import logger
from zgrab import ZGrab, ZGrabCommand, ZGrabResult


class PendingMessage:
    def __init__(self, message: HostMessage, timestamp: datetime):
        self.message = message
        self.timestamp = timestamp


class BannerGrabber:
    def __init__(self, command: ZGrabCommand, message_timeout: int = 300):
        self.command = command
        self.zgrab = ZGrab(command)
        self.db = Database()
        self.queue = AsyncRabbitMQQueueManager()
        self.run_task = None
        self.cleanup_task = None
        self.pending_messages: dict[str, PendingMessage] = {}
        self.message_timeout = message_timeout  # seconds
        self.running = True
        self.tasks = set()

    def _create_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def shutdown(self, signal=None):
        """Cleanup tasks tied to the service's shutdown."""
        if signal:
            logger.info(f"Received exit signal {signal.name}")

        logger.info("Shutting down gracefully...")

        self.running = False

        # Cancel our cleanup task if it's still running
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

        # Cancel ZGrab run task if it's still running
        if self.run_task and not self.run_task.done():
            self.run_task.cancel()

        # Cancel all remaining tasks
        tasks = [t for t in self.tasks if not t.done()]
        if tasks:
            logger.info(f"Cancelling {len(tasks)} outstanding tasks")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Shutdown complete.")

    async def listen(self, port: int | None = None):
        self.run_task = self._create_task(
            self.zgrab.run(callback=self.process_zmap_result)
        )
        self.cleanup_task = self._create_task(self.cleanup_stale_messages())

        logger.info(f"Starting consumer for port: {port}")
        routing_key = f"#.{port if port else '#'}.#.port"

        await self.queue.consume(
            routing_key=routing_key, callback=self.process_incoming
        )  # Blocking

    async def process_incoming(self, port_message: dict):
        logger.debug(
            f"Received RabbitMQ message: {port_message}, now {str(len(self.pending_messages) + 1)} messages in queue"
        )
        try:
            message = from_dict(data_class=HostMessage, data=port_message)
            self.pending_messages[message.ip] = PendingMessage(
                message=message, timestamp=datetime.now()
            )
            await self.zgrab.pipe(message.ip)
        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")

    async def process_zmap_result(self, result: ZGrabResult):
        logger.info(f"Received ZMap result: {result}")
        try:
            pending = self.pending_messages.pop(result.ip, None)
            if pending is None:
                logger.warning(f"No pending message found for IP: {result.ip}")
                return

            message = pending.message
            message.host.banner = Banner(
                service=self.command.service,
                port=self.command.port,
                data=asdict(result.data)[self.command.service],
            )

            await self.publish(message)
            utils.save_banner(self.db, message)

        except Exception as e:
            logger.error(f"Error processing ZMap result: {e}")

    async def cleanup_stale_messages(self):
        while self.running:
            try:
                current_time = datetime.now()
                stale_ips = [
                    ip
                    for ip, pending in self.pending_messages.items()
                    if (current_time - pending.timestamp)
                    > timedelta(seconds=self.message_timeout)
                ]

                for ip in stale_ips:
                    self.pending_messages.pop(ip)
                    logger.warning(
                        f"Removed stale message for IP {ip} after {self.message_timeout} seconds"
                    )

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Continue cleanup even if there's an error

    async def publish(self, message: HostMessage):
        routing_key = (
            f"{message.host.location.country_code}.{message.port}.{message.ip}.banner"
        )
        try:
            await self.queue.publish(routing_key, asdict(message))
        except Exception as e:
            logger.error(f"Error publishing message: {e}")


def main():
    service = os.environ.get("SERVICE")
    if not service:
        logger.error("SERVICE environment variable is required")
        return

    port = os.environ.get("PORT")
    port = int(port) if port else None

    message_timeout = int(os.environ.get("MESSAGE_TIMEOUT", "300"))

    logger.info(f"Starting banner grabber for service: {service}, port: {port}")

    command = ZGrabCommand(service=service, port=port)
    grabber = BannerGrabber(command, message_timeout=message_timeout)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(grabber.listen(port))
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt.")
    finally:
        logger.info("Exiting...")
        loop.run_until_complete(grabber.shutdown())


if __name__ == "__main__":
    main()
