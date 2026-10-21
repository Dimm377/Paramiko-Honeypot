import logging
import os
from typing import Optional

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "honeypot.log")
FORMAT_STRING = "[%(asctime)s] %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class TelemetryLogger:
    """Deep module for honeypot telemetry, event sanitization, and sink management."""

    def __init__(
        self,
        log_file: Optional[str] = None,
        logger_instance: Optional[logging.Logger] = None,
        enable_console: bool = True,
    ):
        if logger_instance is not None:
            self.logger = logger_instance
        else:
            self.logger = logging.getLogger("SSHHoneypot")
            self.logger.setLevel(logging.INFO)

            # Avoid adding duplicate handlers if logger was already configured
            if not self.logger.handlers:
                formatter = logging.Formatter(FORMAT_STRING, datefmt=DATE_FORMAT)

                target_file = log_file if log_file is not None else DEFAULT_LOG_FILE
                file_handler = logging.FileHandler(target_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

                if enable_console:
                    console_handler = logging.StreamHandler()
                    console_handler.setFormatter(formatter)
                    self.logger.addHandler(console_handler)

    def log_connection(self, ip: str, port: int):
        self.logger.info(f"🔌 CONNECTION - {ip}:{port}")

    def log_auth_attempt(self, ip: str, username: str, password: str):
        # Never persist raw submitted passwords. Redact and record telemetry only.
        self.logger.warning(
            f"🔑 AUTH ATTEMPT - IP: {ip} | User: {username} | "
            f"Password length: {len(password)} | Pass: [REDACTED]"
        )

    def log_command(self, ip: str, command: str):
        self.logger.info(f"💻 COMMAND - IP: {ip} | Cmd: {command}")

    def log_disconnect(self, ip: str):
        self.logger.info(f"🔌 DISCONNECT - {ip}")

    def log_error(self, message: str):
        self.logger.error(f"❌ ERROR - {message}")

    def log_info(self, message: str):
        self.logger.info(f"ℹ️  INFO - {message}")


_global_telemetry: Optional[TelemetryLogger] = None


def get_telemetry_logger() -> TelemetryLogger:
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = TelemetryLogger()
    return _global_telemetry


# Backward-compatible convenience functions and global logger reference
logger = get_telemetry_logger().logger


def log_connection(ip: str, port: int):
    get_telemetry_logger().log_connection(ip, port)


def log_auth_attempt(ip: str, username: str, password: str):
    get_telemetry_logger().log_auth_attempt(ip, username, password)


def log_command(ip: str, command: str):
    get_telemetry_logger().log_command(ip, command)


def log_disconnect(ip: str):
    get_telemetry_logger().log_disconnect(ip)


def log_error(message: str):
    get_telemetry_logger().log_error(message)


def log_info(message: str):
    get_telemetry_logger().log_info(message)
