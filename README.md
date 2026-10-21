# Paramiko Honeypot

An educational SSH honeypot built with Paramiko to observe connection, authentication, and command telemetry without granting access to the host system.

Run this project in an isolated local lab.

## Quickstart

### 1. Requirements and setup

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the honeypot

By default, the server binds to `127.0.0.1:2222` in `accept_all` mode:

```bash
python Honeypot.py
```

Console output confirms startup:

```text
[2026-10-21 18:00:00] INFO - ℹ️  INFO - Generating RSA key: server_rsa.key
[2026-10-21 18:00:00] INFO - ℹ️  INFO - RSA key generated successfully
[2026-10-21 18:00:00] INFO - ℹ️  INFO - 🍯 SSH Honeypot started on 127.0.0.1:2222 (mode: accept_all)
[2026-10-21 18:00:00] INFO - ℹ️  INFO - Press Ctrl+C to stop
```

---

## Step-by-Step Testing Guide

Open a second terminal window to run client commands.

### Test 1: Interactive fake shell

Connect using OpenSSH:

```bash
ssh -p 2222 test@127.0.0.1
```

Type any password when prompted. The honeypot logs the attempt and drops you into a simulated Ubuntu 22.04 LTS prompt:

```text
test@127.0.0.1's password: supersecretpassword

Welcome to Ubuntu 22.04.3 LTS

root@ubuntu-server:~$ whoami
root
root@ubuntu-server:~$ pwd
/root
root@ubuntu-server:~$ id
uid=0(root) gid=0(root) groups=0(root)
root@ubuntu-server:~$ ls
Desktop  Documents  Downloads  Music  Pictures  Videos
root@ubuntu-server:~$ cat /etc/shadow
cat: No such file or directory
root@ubuntu-server:~$ exit
Connection to 127.0.0.1 closed.
```

Terminal controls supported:
- Backspace (`\x7f` and `\b`)
- `Ctrl+C` clears the current buffer and reprompts
- `Ctrl+D` closes the session
- Arrow keys and ANSI escape codes are stripped without corrupting input

### Test 2: Non-interactive automated command

Simulate automated scanners or bot scripts that run a command directly without an interactive shell:

```bash
ssh -p 2222 test@127.0.0.1 whoami
```

Output:
```text
root
```

The honeypot answers the command, returns exit code 0, and closes the channel cleanly.

### Test 3: Credential capture mode (`reject_all`)

Stop the running server with `Ctrl+C`, then start it with `HONEYPOT_AUTH_MODE=reject_all`:

```bash
HONEYPOT_AUTH_MODE=reject_all python Honeypot.py
```

Try connecting:

```bash
ssh -p 2222 test@127.0.0.1
```

Client output:
```text
test@127.0.0.1's password: 
Permission denied (password).
```

Server log records the attempt, redacts the password, and refuses entry:

```text
[2026-10-21 18:05:00] WARNING - 🔑 AUTH ATTEMPT - IP: 127.0.0.1 | User: test | Password length: 8 | Pass: [REDACTED]
```

### Test 4: Reading telemetry logs

All events are appended to `honeypot.log`:

```bash
tail -f honeypot.log
```

Example log entries:

```text
[2026-10-21 18:00:10] INFO - 🔌 CONNECTION - 127.0.0.1:45120
[2026-10-21 18:00:12] WARNING - 🔑 AUTH ATTEMPT - IP: 127.0.0.1 | User: admin | Password length: 14 | Pass: [REDACTED]
[2026-10-21 18:00:15] INFO - 💻 COMMAND - IP: 127.0.0.1 | Cmd: whoami
[2026-10-21 18:00:20] INFO - 💻 COMMAND - IP: 127.0.0.1 | Cmd: ls
[2026-10-21 18:00:25] INFO - 🔌 DISCONNECT - 127.0.0.1
```

Raw passwords are never stored. The logger records password character count and tags the value as `[REDACTED]`.

---

## Configuration Reference

Set these environment variables before starting the script:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `HONEYPOT_HOST` | `127.0.0.1` | Bind IP address. Keep set to localhost for safe local experimentation. |
| `HONEYPOT_PORT` | `2222` | TCP port to listen on. |
| `HONEYPOT_AUTH_MODE` | `accept_all` | `accept_all` accepts passwords to study shell interaction.<br>`reject_all` rejects logins to study brute-force credential patterns. |
| `HONEYPOT_MAX_WORKERS` | `50` | Maximum worker threads in the connection pool to prevent connection exhaustion. |
| `HONEYPOT_KEY_FILE` | `server_rsa.key` | Path to private host key. Generated once and cached in memory. |

Example running on a custom port with 20 workers:

```bash
HONEYPOT_PORT=22222 HONEYPOT_MAX_WORKERS=20 python Honeypot.py
```

---

## Architecture

The codebase follows the deep-module design pattern, isolating transport logic behind narrow seams:

- `HoneypotServer` (`Honeypot.py`): Manages the socket lifecycle, caches the RSA host key in memory at startup, and limits concurrent connections via `ThreadPoolExecutor`.
- `HoneypotSession` (`ssh_server.py`): Accepts raw client sockets, coordinates Paramiko transport negotiation and authentication callbacks, and ensures sockets and channels are closed in `finally` blocks.
- `TerminalStream` (`ssh_server.py`): State-machine stream parser that buffers chunked packet input, normalizes newlines, handles backspaces, and strips ANSI escape sequences.
- `CommandDispatcher` (`ssh_server.py`): Maps simulated Linux commands (`ls`, `whoami`, `id`, `pwd`, `uname`, `cat`) to mock responses and flags session exit signals.
- `TelemetryLogger` (`logger.py`): Structured telemetry module with lazy handler initialization, automated password redaction, and mockable sink support for unit testing without filesystem side effects.

---

## Automated Tests

Run the full pytest suite:

```bash
pytest tests/ -v
```

All 22 unit and end-to-end integration tests should pass:

```text
tests/test_integration.py::test_e2e_non_interactive_exec PASSED
tests/test_integration.py::test_e2e_interactive_shell_command PASSED
tests/test_logger.py::test_telemetry_logger_in_memory_sink PASSED
tests/test_logger.py::test_auth_attempt_redacts_password PASSED
tests/test_logger.py::test_convenience_functions_work_and_record PASSED
tests/test_server_daemon.py::test_load_or_generate_key_creates_and_loads PASSED
tests/test_server_daemon.py::test_honeypot_server_initialization PASSED
tests/test_server_daemon.py::test_honeypot_server_connection_dispatch PASSED
tests/test_session.py::test_ssh_server_interface_auth_modes PASSED
tests/test_session.py::test_ssh_server_interface_channel_request PASSED
tests/test_session.py::test_ssh_server_interface_exec_request PASSED
tests/test_session.py::test_honeypot_session_resource_cleanup_on_exception PASSED
tests/test_session.py::test_honeypot_session_successful_shell_invocation PASSED
tests/test_terminal.py::test_command_dispatcher_known_commands PASSED
tests/test_terminal.py::test_command_dispatcher_unknown_command PASSED
tests/test_terminal.py::test_command_dispatcher_exit_commands PASSED
tests/test_terminal.py::test_terminal_stream_chunked_input PASSED
tests/test_terminal.py::test_terminal_stream_pasted_multibyte_command PASSED
tests/test_terminal.py::test_terminal_stream_backspace PASSED
tests/test_terminal.py::test_terminal_stream_ctrl_c PASSED
tests/test_terminal.py::test_terminal_stream_ctrl_d_eof PASSED
tests/test_terminal.py::test_terminal_stream_ansi_arrow_keys_filtered PASSED
```

---

## Disclaimer

For educational and research use in authorized, isolated environments only. Do not expose this service to the public internet without proper network isolation and legal authorization.
