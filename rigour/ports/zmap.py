from dataclasses import dataclass

from common.subprocess import AsyncSubprocessBase


class ZMapCommand:
    def __init__(self, ports: str, networks: str):
        self.ports = ports
        self.networks = networks

    def build(self):
        return [
            "zmap",
            "-p",
            self.ports,
            "--output-module=json",  # Output in JSON format
            "--quiet",  # Suppress status updates
            "--rate=200",  # Send 100 packets per second
            '--output-filter="success = 1"',  # Filter successful results
            self.networks
        ]


@dataclass
class ZMapResult:
    saddr: str
    sport: int


class ZMap(AsyncSubprocessBase[ZMapResult]):
    def __init__(self, command: ZMapCommand):
        super().__init__(command, enable_piping=False)

    async def _parse_result(self, result: dict) -> ZMapResult:
        # Source port is not added when only one port is scanned
        # so it's added manually here
        if "," not in self.command.ports and "-" not in self.command.ports:
            result["sport"] = int(self.command.ports)

        return ZMapResult(**result)
