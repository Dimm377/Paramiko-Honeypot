# Paramiko Honeypot Testing Guide

A step-by-step walkthrough for verifying connection handling, fake shell simulation, credential capture, and telemetry logging in an isolated local lab.

## Prerequisites and Setup

Requires Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Starting the Honeypot

Start the server in your primary terminal window:

```bash
python Honeypot.py
```

Console output confirms startup on `127.0.0.1:2222`:

```text
[2026-10-21 18:00:00] INFO - ℹ️  INFO - Generating RSA key: server_rsa.key
[2026-10-21 18:00:00] INFO - ℹ️  INFO - RSA key generated successfully
[2026-10-21 18:00:00] INFO - ℹ️  INFO - 🍯 SSH Honeypot started on 127.0.0.1:2222 (mode: accept_all)
[2026-10-21 18:00:00] INFO - ℹ️  INFO - Press Ctrl+C to stop
```

Keep this process running and open a second terminal for the client tests below.

---

## Test Scenarios

### Test 1: Interactive fake shell

Connect using any standard OpenSSH client:

```bash
ssh -p 2222 test@127.0.0.1
```

Type any password when prompted. The honeypot accepts authentication and drops the session into an emulated Ubuntu 22.04 LTS prompt:

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

Supported terminal controls:
- Backspace (`\x7f` and `\b`) removes characters from the buffer.
- `Ctrl+C` prints `^C`, clears the buffer, and returns a fresh prompt.
- `Ctrl+D` closes the session cleanly.
- Arrow keys and ANSI escape sequences are stripped to prevent buffer corruption.

### Test 2: Non-interactive automated command

Simulate automated scanners or bot scripts executing a single command directly:

```bash
ssh -p 2222 test@127.0.0.1 whoami
```

Output:
```text
root
```

The honeypot returns the command response, sets exit status 0, and closes the channel cleanly.

### Test 3: Credential capture mode (`reject_all`)

Stop the honeypot in Terminal 1 with `Ctrl+C`, then start it in `reject_all` mode:

```bash
HONEYPOT_AUTH_MODE=reject_all python Honeypot.py
```

In Terminal 2, attempt connection:

```bash
ssh -p 2222 test@127.0.0.1
```

Client output:
```text
test@127.0.0.1's password: 
Permission denied (password).
```

Server output records the attempt, redacts the password, and refuses authentication:

```text
[2026-10-21 18:05:00] WARNING - 🔑 AUTH ATTEMPT - IP: 127.0.0.1 | User: test | Password length: 8 | Pass: [REDACTED]
```

### Test 4: Inspecting telemetry logs

All activity is appended to `honeypot.log`:

```bash
tail -f honeypot.log
```

Example output:

```text
[2026-10-21 18:00:10] INFO - 🔌 CONNECTION - 127.0.0.1:45120
[2026-10-21 18:00:12] WARNING - 🔑 AUTH ATTEMPT - IP: 127.0.0.1 | User: admin | Password length: 14 | Pass: [REDACTED]
[2026-10-21 18:00:15] INFO - 💻 COMMAND - IP: 127.0.0.1 | Cmd: whoami
[2026-10-21 18:00:20] INFO - 💻 COMMAND - IP: 127.0.0.1 | Cmd: ls
[2026-10-21 18:00:25] INFO - 🔌 DISCONNECT - 127.0.0.1
```

Submitted passwords are never stored in plain text. The logger records only the password character count and tags the value as `[REDACTED]`.

### Test 5: Running the automated test suite

Verify all units and end-to-end integration tests:

```bash
pytest tests/ -v
```

All 22 tests should pass:

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
