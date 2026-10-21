import time
import threading
import paramiko
import pytest
from Honeypot import HoneypotServer


@pytest.fixture(scope="module")
def honeypot_test_server():
    server = HoneypotServer(host="127.0.0.1", port=0, auth_mode="accept_all")
    # Start on ephemeral port
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    # Wait for server socket to bind
    for _ in range(50):
        if server.server_socket is not None:
            break
        time.sleep(0.05)

    port = server.server_socket.getsockname()[1]
    yield ("127.0.0.1", port)

    server.stop()


def test_e2e_non_interactive_exec(honeypot_test_server):
    host, port = honeypot_test_server
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username="tester", password="secretpassword")

    stdin, stdout, stderr = client.exec_command("whoami")
    out = stdout.read().decode().strip()
    assert out == "root"
    client.close()


def test_e2e_interactive_shell_command(honeypot_test_server):
    host, port = honeypot_test_server
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username="shelluser", password="secretpassword")

    shell = client.invoke_shell()
    time.sleep(0.3)
    banner = shell.recv(1024).decode()
    assert "Ubuntu" in banner

    shell.send("pwd\n")
    time.sleep(0.3)
    response = shell.recv(1024).decode()
    assert "/root" in response

    client.close()
