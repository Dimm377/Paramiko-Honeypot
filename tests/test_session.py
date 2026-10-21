from unittest.mock import MagicMock, patch
import paramiko
import pytest
from ssh_server import SSHServerInterface, HoneypotSession


def test_ssh_server_interface_auth_modes():
    # Test accept_all mode
    interface_accept = SSHServerInterface("127.0.0.1", auth_mode="accept_all")
    assert interface_accept.check_auth_password("user", "pass") == paramiko.AUTH_SUCCESSFUL

    # Test reject_all mode
    interface_reject = SSHServerInterface("127.0.0.1", auth_mode="reject_all")
    assert interface_reject.check_auth_password("user", "pass") == paramiko.AUTH_FAILED


def test_ssh_server_interface_channel_request():
    interface = SSHServerInterface("127.0.0.1")
    assert interface.check_channel_request("session", 0) == paramiko.OPEN_SUCCEEDED
    assert interface.check_channel_request("direct-tcpip", 0) == paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


def test_ssh_server_interface_exec_request():
    interface = SSHServerInterface("127.0.0.1")
    mock_channel = MagicMock()

    result = interface.check_channel_exec_request(mock_channel, b"whoami")
    assert result is True
    mock_channel.send.assert_called_with("root\r\n")
    mock_channel.send_exit_status.assert_called_with(0)
    mock_channel.close.assert_called_once()


def test_honeypot_session_resource_cleanup_on_exception():
    mock_socket = MagicMock()
    mock_key = MagicMock()

    with patch("paramiko.Transport") as mock_transport_cls:
        mock_transport = MagicMock()
        mock_transport_cls.return_value = mock_transport
        mock_transport.accept.side_effect = Exception("Transport failure")

        session = HoneypotSession(server_key=mock_key, auth_mode="accept_all")
        session.handle(mock_socket, ("127.0.0.1", 12345))

        # Ensure both transport and socket were closed
        mock_transport.close.assert_called_once()
        mock_socket.close.assert_called_once()


def test_honeypot_session_successful_shell_invocation():
    mock_socket = MagicMock()
    mock_key = MagicMock()
    mock_channel = MagicMock()

    with patch("paramiko.Transport") as mock_transport_cls, \
         patch("ssh_server.FakeShell") as mock_shell_cls:
        mock_transport = MagicMock()
        mock_transport_cls.return_value = mock_transport
        mock_transport.accept.return_value = mock_channel
        
        mock_shell = MagicMock()
        mock_shell_cls.return_value = mock_shell

        session = HoneypotSession(server_key=mock_key, auth_mode="accept_all")
        # Trigger event in interface when start_server is called
        def fake_start_server(server):
            server.event.set()
        mock_transport.start_server.side_effect = fake_start_server

        session.handle(mock_socket, ("127.0.0.1", 12345))

        mock_shell.handle.assert_called_once()
        mock_channel.close.assert_called_once()
        mock_transport.close.assert_called_once()
        mock_socket.close.assert_called_once()
