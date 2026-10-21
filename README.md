# Paramiko Honeypot

An educational SSH honeypot designed for observing connection, authentication, and command telemetry using Paramiko.

This project provides a safe, emulated SSH environment. It does not grant access to the host operating system and should only be operated in an isolated lab network or local testing environment.

## Requirements

- Python 3.9 or newer
- `pip`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Running the Honeypot

The default configuration safely binds to localhost on port `2222` with interactive fake shell observation enabled (`accept_all`):

```bash
python Honeypot.py
```

### Configuration Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `HONEYPOT_HOST` | `127.0.0.1` | Network interface to bind. Keep on localhost for safe local experimentation. |
| `HONEYPOT_PORT` | `2222` | TCP port to listen on. |
| `HONEYPOT_AUTH_MODE` | `accept_all` | `accept_all`: logs credentials and accepts login to observe fake shell activity.<br>`reject_all`: logs credentials and rejects login (telemetry-only). |
| `HONEYPOT_MAX_WORKERS` | `50` | Maximum concurrent worker threads in the connection pool. |
| `HONEYPOT_KEY_FILE` | `server_rsa.key` | Path to the cached RSA host private key. |

Example running in telemetry-only credential capture mode:

```bash
HONEYPOT_AUTH_MODE=reject_all python Honeypot.py
```

## Testing Connections

### 1. Interactive Fake Shell

Connect using any standard SSH client:

```bash
ssh -p 2222 test@127.0.0.1
```

Once connected, you will receive an emulated Ubuntu 22.04 LTS prompt:
```text
test@127.0.0.1's password: (any password)

Welcome to Ubuntu 22.04.3 LTS

root@ubuntu-server:~$ whoami
root
root@ubuntu-server:~$ ls
Desktop  Documents  Downloads  Music  Pictures  Videos
root@ubuntu-server:~$ exit
```

### 2. Non-Interactive Command Execution

Automated scanners and scripts executing single commands are supported:

```bash
ssh -p 2222 test@127.0.0.1 whoami
```

Outputs:
```text
root
```

## Architecture & Deep Modules

- **`HoneypotSession`**: Encapsulates Paramiko transport handshake, channel routing, and interactive shell handling behind a single deep interface with guaranteed socket cleanup.
- **`TerminalStream`**: State-machine parser that cleanly handles chunked inputs, CRLF normalization, backspaces, control interrupts (Ctrl+C, Ctrl+D), and ANSI escape sequence filtering.
- **`TelemetryLogger`**: Structured logging module with lazy configuration, password redaction, and mockable sink support for tests without import-time file system side-effects.
- **`HoneypotServer`**: ThreadPool-bounded daemon lifecycle with cached RSA key generation and graceful signal handling (`SIGINT`/`SIGTERM`).

## Running Tests

Run the comprehensive unit and integration test suite:

```bash
pytest tests/ -v
```

## Logging & Data Handling

Events are logged to `honeypot.log` and the console. Authentication events record source IP, username, and password length. Submitted passwords are always redacted by default:

```text
[2026-01-01 12:00:00] WARNING - 🔑 AUTH ATTEMPT - IP: 127.0.0.1 | User: root | Password length: 12 | Pass: [REDACTED]
[2026-01-01 12:00:02] INFO - 💻 COMMAND - IP: 127.0.0.1 | Cmd: whoami
```

## Disclaimer

For educational and research use in an authorized, isolated environment only. Never expose to public networks without proper containment, legal clearance, and network monitoring.
