from dataclasses import dataclass
from datetime import datetime

from common.subprocess import AsyncSubprocessBase
from dacite import from_dict


@dataclass
class ZGrabCommand:
    service: str
    port: int | None = None

    def build(self) -> list[str]:
        args = ["zgrab2", self.service]
        # args = ["docker", "run", "--rm", "-i", "ghcr.io/zmap/zgrab2", self.service]
        if self.port:
            args += ["--port", str(self.port)]

        args.append("--flush")

        return args


@dataclass
class ZGrabService:
    status: str
    protocol: str
    timestamp: datetime
    error: str | None = None
    result: dict | None = None


@dataclass
class ZGrabData:
    amqp091: ZGrabService | None = None
    bacnet: ZGrabService | None = None
    banner: ZGrabService | None = None
    dnp3: ZGrabService | None = None
    fox: ZGrabService | None = None
    ftp: ZGrabService | None = None
    http: ZGrabService | None = None
    imap: ZGrabService | None = None
    ipp: ZGrabService | None = None
    jarm: ZGrabService | None = None
    modbus: ZGrabService | None = None
    mongodb: ZGrabService | None = None
    mssql: ZGrabService | None = None
    multiple: ZGrabService | None = None
    mysql: ZGrabService | None = None
    ntp: ZGrabService | None = None
    oracle: ZGrabService | None = None
    pop3: ZGrabService | None = None
    postgres: ZGrabService | None = None
    redis: ZGrabService | None = None
    siemens: ZGrabService | None = None
    smb: ZGrabService | None = None
    smtp: ZGrabService | None = None
    ssh: ZGrabService | None = None
    telnet: ZGrabService | None = None
    tls: ZGrabService | None = None


@dataclass
class ZGrabResult:
    ip: str
    data: ZGrabData


class ZGrab(AsyncSubprocessBase[ZGrabResult]):
    def __init__(self, command: ZGrabCommand):
        super().__init__(command, enable_piping=True)

    async def _parse_result(self, result: dict) -> ZGrabResult:
        """Parse the ZGrab result into ZGrabResult dataclass."""
        result["data"][self.command.service]["timestamp"] = datetime.fromisoformat(
            result["data"][self.command.service]["timestamp"]
        )

        return from_dict(data_class=ZGrabResult, data=result)
