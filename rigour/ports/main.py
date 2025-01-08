import asyncio
import os
from dataclasses import asdict
from datetime import datetime

import geoip2.database
import geoip2.errors
from common import utils
from common.database.mongodb import Database
from common.queue.rabbitmq_asyncio import AsyncRabbitMQQueueManager
from common.types import Host, HostMessage, Location
from common.config import Config
from loguru import logger
from zmap import ZMap, ZMapCommand, ZMapResult


def get_location(ip: str, reader: geoip2.database.Reader) -> Location:
    try:
        geoip = reader.city(ip)
        return Location(
            country_code=geoip.continent.code,  # type: ignore
            continent_name=geoip.continent.names.get("en"),
            country_name=geoip.country.names.get("en"),
            accuracy_radius=geoip.location.accuracy_radius,
            latitude=geoip.location.latitude,
            longitude=geoip.location.longitude,
        )
    except geoip2.errors.AddressNotFoundError:
        logger.warning(f"IP {ip} not found in database")
        return Location("?")


def save(db: Database, message: HostMessage) -> None:
    logger.debug(f"Saving host to database for IP: {message.ip}, Port: {message.port}")
    now = datetime.now()
    db.scans.update_one(
        {"ip": message.ip},
        {
            "$set": {"location": asdict(message.host.location), "updated_at": now},
            "$setOnInsert": {"first_seen": now},
        },
        upsert=True,
    )


def main():
    db = Database()
    queue = AsyncRabbitMQQueueManager()
    reader = geoip2.database.Reader("geolite2-city.mmdb")
    ports = Config.get_ports()
    networks = Config.get_networks()
    
    logger.info(f"Starting port scanner for port/s: {ports}")

    async def callback(result: ZMapResult) -> None:
        print(f"Received ZMap result: {result}")
        location = get_location(result.saddr, reader)
        host = HostMessage(result.saddr, result.sport, Host(location=location))

        # {country}.{port}.{ip}.port
        route_key = utils.route_key_from_host_message(host, "port")
        await queue.publish(route_key, asdict(host))
        save(db, host)

    command = ZMapCommand(ports,networks)
    zmap = ZMap(command)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(zmap.run(callback))
    loop.close()


if __name__ == "__main__":
    main()
