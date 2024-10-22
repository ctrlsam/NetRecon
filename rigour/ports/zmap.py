import json
import subprocess
from dataclasses import dataclass

from loguru import logger


class ZMapCommand:
    def __init__(self, ports: str):
        self.ports = ports

    def build(self):
        return [
            "zmap",
            "-p",
            self.ports,
            "--output-module=json",  # Output in JSON format
            "--quiet",  # Suppress status updates
            "--rate=100",  # Send 100 packets per second
        ]


@dataclass
class ZMapResult:
    saddr: str
    sport: int


class ZMap:
    def __init__(self, command: ZMapCommand):
        self.command = command

    def run(self, callback: callable):  # type: ignore
        # Run ZMap as a subprocess
        process = subprocess.Popen(
            self.command.build(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,  # Line-buffered
        )

        # Read and process the output line by line
        for line in process.stdout:  # type: ignore
            line = line.strip()
            if not line:
                continue

            raw_result = json.loads(line)

            # Source port is not added when only one port is scanned
            # so it's added manually here
            if "," not in self.command.ports and "-" not in self.command.ports:
                raw_result["sport"] = int(self.command.ports)

            # Skip if source address or port is not available
            # TODO: research why this occurs
            elif "sport" not in raw_result:
                continue

            callback(ZMapResult(**raw_result))

        # Wait for the process to finish and check for errors
        process.wait()
        stderr = process.stderr.read()  # type: ignore
        if stderr:
            logger.error(stderr)
