import datetime
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Vulnerability:
    name: str
    title: str
    version: str
    link: str
    # TODO: This should be linked to the service and port


@dataclass
class Location:
    country_code: str | None = None
    continent_name: str | None = None
    country_name: str | None = None
    accuracy_radius: int | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class Banner:
    service: str
    port: int | None
    data: dict


@dataclass
class Host:
    location: Location
    banner: Banner | None = None
    vulnerabilities: list[Vulnerability] | None = None


@dataclass
class HostMessage:
    ip: str
    port: int
    host: Host


class DBHost(BaseModel):
    ip: str
    location: Location
    banners: dict[str, Banner] = {}
    vulnerabilities: list[Vulnerability] = []
    updated_at: datetime.datetime
    first_seen: datetime.datetime

    class Config:
        from_attributes = True  # Allows compatibility with ORM objects
        extra = "ignore"  # Ignores extra fields not defined in the model
