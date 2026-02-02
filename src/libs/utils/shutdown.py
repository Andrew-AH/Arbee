from datetime import datetime
import platform
import subprocess

from libs.utils.log import get_logger

log = get_logger(logs_to_console=True)


def schedule_windows_shutdown(shutdown_time: datetime):
    os_name = platform.system().lower()

    if "windows" in os_name:
        log.info(f"Received shutdown datetime: {shutdown_time}")
        current_time = datetime.now()
        delay = (shutdown_time - current_time).total_seconds()

        if delay <= 0:
            log.error("Shutdown time is in the past. Please provide a future datetime.")
            return

        # Cancel any existing scheduled shutdowns
        subprocess.run(
            "shutdown -a",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Windows shutdown command (in seconds)
        shutdown_command = f"shutdown -s -f -t {int(delay)}"
        log.info(f"Scheduling shutdown on Windows in {int(delay)} seconds")
        subprocess.run(shutdown_command, shell=True)
