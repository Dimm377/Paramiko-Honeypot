import os
import socket
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from Honeypot import load_or_generate_key, HoneypotServer


def test_load_or_generate_key_creates_and_loads():
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "test_server.key")
        assert not os.path.exists(key_path)

        key1 = load_or_generate_key(key_path)
        assert os.path.exists(key_path)
        assert key1 is not None

        # Second call loads the existing file
        key2 = load_or_generate_key(key_path)
        assert key2.get_base64() == key1.get_base64()


def test_honeypot_server_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "test_server.key")
        server = HoneypotServer(
            host="127.0.0.1",
            port=2222,
            auth_mode="accept_all",
            max_workers=10,
            key_file=key_path,
        )

        assert server.host == "127.0.0.1"
        assert server.port == 2222
        assert server.max_workers == 10
        assert server.server_key is not None
        assert server.session_handler is not None

        server.stop()


def test_honeypot_server_connection_dispatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        key_path = os.path.join(tmpdir, "test_server.key")
        server = HoneypotServer(
            host="127.0.0.1",
            port=0,
            auth_mode="accept_all",
            max_workers=5,
            key_file=key_path,
        )

        mock_socket = MagicMock()
        mock_addr = ("10.0.0.1", 54321)

        with patch.object(server.session_handler, "handle") as mock_handle:
            server.dispatch_client(mock_socket, mock_addr)
            server.executor.shutdown(wait=True)
            mock_handle.assert_called_once_with(mock_socket, mock_addr)

        server.stop()
