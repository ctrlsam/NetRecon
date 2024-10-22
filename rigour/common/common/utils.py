import json
from dataclasses import asdict
from datetime import datetime

from common.database.mongodb import Database
from common.types import HostMessage
from loguru import logger


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):  # type: ignore
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def route_key_from_host_message(message: HostMessage, data_type: str) -> str:
    return (
        f"{message.host.location.country_code}.{message.port}.{message.ip}.{data_type}"
    )


# TODO: move this elsewhere
def save_banner(db: Database, message: HostMessage) -> None:
    assert message.host.banner is not None
    logger.debug(
        f"Saving banner to database for IP: {message.ip}, Port: {message.port}"
    )

    now = datetime.now()

    db.scans.update_one(
        {"ip": message.ip},
        {
            "$set": {
                f"banners.{message.host.banner.service}": asdict(message.host.banner),
                "updated_at": now,
            }
        },
        upsert=True,
    )


# TODO: move this elsewhere
def save_vulnerability(db: Database, message: HostMessage) -> None:
    assert message.host.vulnerabilities is not None
    logger.debug(
        f"Saving vulnerabilities to database for IP: {message.ip}, Port: {message.port}"
    )

    now = datetime.now()

    db.scans.update_one(
        {"ip": message.ip},
        {
            "$set": {
                "vulnerabilities": [asdict(v) for v in message.host.vulnerabilities],
                "updated_at": now,
            }
        },
        upsert=True,
    )
