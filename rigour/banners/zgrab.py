import json
import queue
import select
import subprocess
import threading
from dataclasses import dataclass
from queue import Queue

from common.queue.rabbitmq import RabbitMQQueueManager
from loguru import logger


@dataclass
class ZGrabCommand:
    service: str
    port: int

    def build(self) -> list[str]:
        return [
            "zgrab2",
            self.service,
            "-p",
            str(self.port),
        ]


@dataclass
class ZGrabResult:
    ip: str
    data: dict | None = None


class ZGrab:
    def __init__(self, command: ZGrabCommand):
        self.command = command
        self.process = None
        self.input_queue = Queue()
        self.is_running = False

        # Create a thread-local storage for the connection and channel
        # This prevents thread errors when using the same connection in multiple threads
        self.queue_manager = RabbitMQQueueManager()

    def run(self, callback: callable):  # type: ignore
        self.is_running = True
        self.process = subprocess.Popen(
            self.command.build(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
        )

        stdout_thread = threading.Thread(
            target=self.read, args=(self.process, callback)
        )
        stdout_thread.daemon = True
        stdout_thread.start()

        stdin_thread = threading.Thread(target=self.write)
        stdin_thread.daemon = True
        stdin_thread.start()

        # # Wait for the process to finish and check for errors
        # self.process.wait()
        # stderr = self.process.stderr.read()
        # if stderr:
        #     logger.error(stderr)

    def pipe(self, ip: str):
        self.input_queue.put(ip)
        if qsize := self.input_queue.qsize() > 10:
            logger.warning(f"Input queue is exceeding {qsize} items!")

    def read(self, process: subprocess.Popen, callback: callable):  # type: ignore
        logger.info("Starting to read ZGrab output")
        while True:
            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if ready:
                line = process.stdout.readline()  # type: ignore
                if not line:
                    logger.debug("ZGrab output ended")
                    break  # EOF
                line = line.strip()
                if line:
                    try:
                        result = json.loads(line)
                        callback(self.parse_result(result))
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON: {line}")

    def write(self):
        logger.info("Starting to write IPs to ZGrab")
        while True:
            try:
                ip = self.input_queue.get(timeout=1)
                logger.debug(f"Writing IP to ZGrab: {ip}")
                self.process.stdin.write(f"{ip}\n")  # type: ignore
                self.process.stdin.flush()  # type: ignore
            except queue.Empty:
                continue
            except BrokenPipeError:
                logger.error("Broken pipe when writing to ZGrab")
                break

    def parse_result(self, result: dict) -> ZGrabResult:
        return ZGrabResult(ip=result.get("ip", ""), data=result.get("data"))

    def close(self):
        self.is_running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
