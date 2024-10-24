import asyncio
import re
from dataclasses import asdict

from common import utils
from common.database.mongodb import Database
from common.queue.rabbitmq_asyncio import AsyncRabbitMQQueueManager
from common.types import HostMessage
from dacite import from_dict
from loguru import logger
from vuln_detector import VulnerabilityDetector


class VulnScanner:
    def __init__(self) -> None:
        self.db = Database()
        self.queue = AsyncRabbitMQQueueManager()
        self.detector = VulnerabilityDetector()
        self.software_version_pattern = re.compile(r"(\w+)[/ ]([\d.]+)")

    async def listen(self) -> None:
        # {country}.{port}.{ip}.banner
        routing_key = "#.#.#.banner"
        await self.queue.consume(routing_key=routing_key, callback=self.process_banners)

    async def process_banners(self, port_message: dict) -> None:
        logger.debug(f"Received RabbitMQ message: {port_message}")
        message = from_dict(data_class=HostMessage, data=port_message)

        assert message.host.banner is not None
        if message.host.banner.service != "http":
            logger.debug(f"Skipping non-HTTP service: {message.host.banner.service}")
            return

        server_header = self.get_server_header(message)
        if server_header is None:
            logger.debug("Skipping as server header not in HTTP response")
            return

        software = self.get_software_version(server_header)
        if not software:
            logger.debug("Skipping as software version not found in server header")
            return

        vulnerabilities = self.detector.scan(*software)
        if not vulnerabilities:
            logger.debug("No vulnerabilities found")
            return

        message.host.vulnerabilities = vulnerabilities

        await self.publish(message)
        utils.save_vulnerability(self.db, message)

    def get_server_header(self, message: HostMessage) -> str | None:
        assert message.host.banner is not None
        try:
            return message.host.banner.data["result"]["response"]["headers"]["server"][
                0
            ]
        except (KeyError, TypeError, IndexError):
            return None

    def get_software_version(self, server_header: str) -> tuple[str, str] | None:
        match = self.software_version_pattern.search(server_header)
        if match is None:
            return None
        return match.groups()  # type: ignore

    async def publish(self, message: HostMessage) -> None:
        route_key = utils.route_key_from_host_message(message, "vuln")
        await self.queue.publish(route_key, asdict(message))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(VulnScanner().listen())
    loop.run_forever()
