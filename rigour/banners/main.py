import os
from dataclasses import asdict

from common import utils
from common.database.mongodb import Database
from common.queue.rabbitmq import RabbitMQQueueManager
from common.types import Banner, HostMessage
from dacite import from_dict
from loguru import logger
from zgrab import ZGrab, ZGrabCommand, ZGrabResult


class BannerGrabber:
    def __init__(self, command: ZGrabCommand):
        self.command = command
        self.zgrab = ZGrab(command)
        self.db = Database()
        self.queue = RabbitMQQueueManager()
        self.host_cache = {}

    def listen(self, port: int | None = None):
        self.zgrab.run(callback=self.process_zmap_result)
        self._start_consumer(port)

    def _start_consumer(self, port: int | None):
        logger.info(f"Starting consumer for port: {port}")
        routing_key = f"#.{port if port else '#'}.#.port"
        self.queue.consume(routing_key=routing_key, callback=self.process_incoming)

    def process_incoming(self, port_message: dict):
        logger.debug(f"Received RabbitMQ message: {port_message}")
        message = from_dict(data_class=HostMessage, data=port_message)
        self.host_cache[message.ip] = message
        self.zgrab.pipe(message.ip)

    def process_zmap_result(self, result: ZGrabResult):
        logger.debug(f"Received ZMap result: {result}")
        message = self.host_cache.pop(result.ip)
        if message is not None:
            # Add the banner to the message
            message.host.banner = Banner(
                service=self.command.service,
                port=self.command.port,
                data=asdict(result)["data"][self.command.service],
            )
            self.publish(message)
            utils.save_banner(self.db, message)
        else:
            logger.warning(f"Port information not found for IP: {result.ip}")

    def publish(self, message: HostMessage):
        # {country}.{port}.{ip}.banners
        routing_key = (
            f"{message.host.location.country_code}.{message.port}.{message.ip}.banner"
        )
        self.queue.publish(routing_key, asdict(message))


def main():
    service = os.environ.get("SERVICE")
    if not service:
        logger.error("SERVICE environment variable is required")
        return

    port = int(os.environ.get("PORT", "80"))

    logger.info(f"Starting banner grabber for service: {service}, port: {port}")

    command = ZGrabCommand(service=service, port=port)
    grabber = BannerGrabber(command)
    grabber.listen(port)


if __name__ == "__main__":
    main()
