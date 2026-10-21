# Paramiko Honeypot

An educational SSH honeypot built with Paramiko to observe connection, authentication, and command telemetry without granting access to the host system.

Run this project in an isolated local lab.

## Quickstart

### 1. Setup

Requires Python 3.9 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run

Start the honeypot on `127.0.0.1:2222`:

```bash
python Honeypot.py
```

---

## Testing Guide

Detailed step-by-step instructions for trying the interactive fake shell, testing scanner command execution, capturing brute-force attempts, and reading telemetry logs are documented in:

👉 **[TESTING.md](TESTING.md)**

Quick connection test:

```bash
ssh -p 2222 test@127.0.0.1
```

---

## Configuration Reference

Configure the honeypot using environment variables before running:

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

All 22 unit and end-to-end integration tests should pass.

---

## Disclaimer

For educational and research use in authorized, isolated environments only. Do not expose this service to the public internet without proper network isolation and legal authorization.
