import asyncio
import json
from typing import Generic, TypeVar

from loguru import logger

T = TypeVar("T")


class AsyncSubprocessBase(Generic[T]):
    def __init__(self, command, enable_piping: bool = False):
        self.command = command
        self.process: asyncio.subprocess.Process | None = None
        self._stdin_lock = asyncio.Lock()
        self._enable_piping = enable_piping
        self._stdout_task = None
        self._stderr_task = None

    async def run(self, callback: callable):
        """Run the subprocess asynchronously and process output line-by-line."""
        args = self.command.build()

        # Start the subprocess with appropriate pipes
        logger.debug(f"Starting subprocess with args: {' '.join(args)}")
        self.process = await self._create_subprocess(args)

        # Create asynchronous tasks for reading stdout and stderr
        self._stdout_task = asyncio.create_task(self._read_stdout(callback))
        self._stderr_task = asyncio.create_task(self._read_stderr())

        if not self._enable_piping:
            # If piping is not enabled, wait for process to complete
            await self.process.wait()
            await asyncio.gather(self._stdout_task, self._stderr_task)

            return_code = self.process.returncode
            if return_code != 0:
                logger.warning(f"Subprocess exited with return code {return_code}")

    async def _create_subprocess(self, args):
        """Create subprocess with appropriate pipes."""
        stdin_pipe = asyncio.subprocess.PIPE if self._enable_piping else None
        return await asyncio.create_subprocess_exec(
            *args,
            stdin=stdin_pipe,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def _read_stderr(self):
        """Asynchronously reads lines from the subprocess's stderr."""
        if not self.process or not self.process.stderr:
            return

        try:
            async for line in self.process.stderr:
                line = line.strip()
                if line:
                    logger.error(f"Subprocess stderr: {line.decode()}")
        except Exception as e:
            logger.error(f"Error reading stderr: {e}")

    async def _read_stdout(self, callback: callable):
        """Reads the output from the subprocess asynchronously, handling large lines."""
        if not self.process or not self.process.stdout:
            return

        buffer = b""
        try:
            while True:
                chunk = await self.process.stdout.read(4096)  # Read in 4KB chunks
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    await self._process_line(line, callback)

            # Process any remaining data in the buffer
            if buffer:
                await self._process_line(buffer, callback)
        except Exception as e:
            logger.exception(f"Error reading stdout: {e}")

    async def _process_line(self, line: bytes, callback: callable):
        """Processes a single line from stdout."""
        line = line.strip()
        if not line:
            return

        try:
            result = json.loads(line)
            parsed_result = await self._parse_result(result)
            if parsed_result:
                await callback(parsed_result)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {line}")
        except Exception as e:
            logger.exception(f"Error processing line: {e}")

    async def _parse_result(self, result: dict) -> T:
        """Parse the raw result into appropriate type. Must be implemented by subclasses."""
        raise NotImplementedError

    async def pipe(self, data: str):
        """Pipe input data into the subprocess asynchronously."""
        if not self._enable_piping:
            logger.error("Piping is not enabled for this subprocess")
            return

        if not self.process or not self.process.stdin:
            logger.error("Cannot pipe: process or stdin not available")
            return

        try:
            async with self._stdin_lock:
                self.process.stdin.write(f"{data}\n".encode())
                await self.process.stdin.drain()
                logger.debug(f"Successfully piped data to subprocess: {data}")
        except Exception as e:
            logger.error(f"Error piping data to subprocess: {e}")

    async def close(self):
        """Close the process and clean up resources."""
        if self.process:
            try:
                # Close stdin first if piping was enabled
                if self._enable_piping and self.process.stdin:
                    self.process.stdin.close()
                    await self.process.stdin.wait_closed()

                # Cancel reading tasks
                if self._stdout_task:
                    self._stdout_task.cancel()
                if self._stderr_task:
                    self._stderr_task.cancel()

                # Terminate the process
                self.process.terminate()
                await self.process.wait()

                logger.info("Subprocess and tasks terminated.")
            except Exception as e:
                logger.error(f"Error closing subprocess: {e}")
