import logging
from datetime import datetime
import os

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "honeypot.log")

logger = logging.getLogger("SSHHoneypot")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_connection(ip: str, port: int):
    logger.info(f"🔌 CONNECTION - {ip}:{port}")

def log_auth_attempt(ip: str, username: str, password: str):
    # Never persist submitted passwords. The honeypot records telemetry only.
    logger.warning(
        f"🔑 AUTH ATTEMPT - IP: {ip} | User: {username} | "
        f"Password length: {len(password)} | Pass: [REDACTED]"
    )

def log_command(ip: str, command: str):
    logger.info(f"💻 COMMAND - IP: {ip} | Cmd: {command}")

def log_disconnect(ip: str):
    logger.info(f"🔌 DISCONNECT - {ip}")

def log_error(message: str):
    logger.error(f"❌ ERROR - {message}")

def log_info(message: str):
    logger.info(f"ℹ️  INFO - {message}")
