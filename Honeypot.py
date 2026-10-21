#!/usr/bin/env python3
import concurrent.futures
import os
import signal
import socket
from typing import Optional, Tuple
import paramiko

from ssh_server import HoneypotSession
from logger import log_error, log_info

HOST = os.getenv("HONEYPOT_HOST", "127.0.0.1")
PORT = int(os.getenv("HONEYPOT_PORT", "2222"))
AUTH_MODE = os.getenv("HONEYPOT_AUTH_MODE", "accept_all")
MAX_WORKERS = int(os.getenv("HONEYPOT_MAX_WORKERS", "50"))
RSA_KEY_FILE = os.getenv("HONEYPOT_KEY_FILE", "server_rsa.key")


def load_or_generate_key(key_file: str = RSA_KEY_FILE) -> paramiko.RSAKey:
    """Loads an existing private key or generates a new 2048-bit RSA key once."""
    if not os.path.exists(key_file):
        log_info(f"Generating RSA key: {key_file}")
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(key_file)
        log_info("RSA key generated successfully")
    return paramiko.RSAKey.from_private_key_file(key_file)


# Backward-compatible alias
def generate_rsa_key() -> paramiko.RSAKey:
    return load_or_generate_key(RSA_KEY_FILE)


class HoneypotServer:
    """Manages server socket lifecycle, worker pool, and cached key state."""

    def __init__(
        self,
        host: str = HOST,
        port: int = PORT,
        auth_mode: str = AUTH_MODE,
        max_workers: int = MAX_WORKERS,
        key_file: str = RSA_KEY_FILE,
    ):
        self.host = host
        self.port = port
        self.auth_mode = auth_mode
        self.max_workers = max_workers
        self.server_key = load_or_generate_key(key_file)
        self.session_handler = HoneypotSession(self.server_key, auth_mode=self.auth_mode)
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="HoneypotWorker",
        )
        self.server_socket: Optional[socket.socket] = None
        self._running = False

    def dispatch_client(self, client_socket: socket.socket, client_addr: Tuple[str, int]):
        self.executor.submit(self.session_handler.handle, client_socket, client_addr)

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self._running = True

            log_info(f"🍯 SSH Honeypot started on {self.host}:{self.port} (mode: {self.auth_mode})")
            log_info("Press Ctrl+C to stop")

            while self._running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    self.dispatch_client(client_socket, client_addr)
                except (socket.error, OSError):
                    break
        except PermissionError:
            log_error(f"Permission denied for port {self.port}. Try port > 1024 or run as root.")
        except OSError as e:
            log_error(f"Socket error on {self.host}:{self.port}: {e}")
        finally:
            self.stop()

    def stop(self):
        if not self._running and self.server_socket is None:
            return
        self._running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        self.executor.shutdown(wait=False, cancel_futures=True)
        log_info("Honeypot server stopped.")


# Backward-compatible connection handler
def handle_connection(client_socket: socket.socket, client_addr: tuple):
    key = load_or_generate_key()
    session = HoneypotSession(key, auth_mode=AUTH_MODE)
    session.handle(client_socket, client_addr)


def main():
    server = HoneypotServer()

    def signal_handler(signum, frame):
        log_info("Shutdown signal received...")
        server.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server.start()


if __name__ == "__main__":
    main()
