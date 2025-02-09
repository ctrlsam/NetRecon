import asyncio
from dataclasses import asdict

from common import utils
from common.database.mongodb import Database
from common.queue.rabbitmq_asyncio import AsyncRabbitMQQueueManager
from common.types import Banner, HostMessage
from dacite import from_dict
from loguru import logger
from mcstatus import JavaServer, status_response


class MinecraftBannerGrabber:
    def __init__(self, port: int = 25565):
        self.db = Database()
        self.queue = AsyncRabbitMQQueueManager()
        self.port = port

    async def listen(self):
        routing_key = f"#.{self.port}.#.port"
        await self.queue.consume(routing_key=routing_key, callback=self.process_port)

    async def process_port(self, port_message: dict) -> None:
        logger.debug(f"Received RabbitMQ message: {port_message}")
        message = from_dict(data_class=HostMessage, data=port_message)

        banner = self.get_mc_banner(message.ip, message.port)
        if banner is None:
            logger.debug("Skipping as no banner found")
            return

        logger.info(f"Found banner: {banner.raw}")
        message.host.banner = Banner(
            service="minecraft", port=message.port, data=dict(banner.raw)
        )

        route_key = utils.route_key_from_host_message(message, "banner")
        await self.queue.publish(route_key, asdict(message))
        utils.save_banner(self.db, message)

    def get_mc_banner(
        self, ip: str, port: int
    ) -> status_response.JavaStatusResponse | None:
        try:
            server = JavaServer(ip, port)
            status = server.status()
        except:
            logger.debug(f"Failed to get status of: {ip}:{port}")
        else:
            return status


if __name__ == "__main__":
    grabber = MinecraftBannerGrabber()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(grabber.listen())
    loop.run_forever()
