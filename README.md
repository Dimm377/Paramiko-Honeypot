# Paramiko Honeypot

A small educational SSH honeypot for studying connection and authentication telemetry with Paramiko.

This project provides a fake SSH shell. It does not grant access to the host system and should only be used in an isolated local lab.

## Requirements

- Python 3.9 or newer
- `pip`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

The safe default binds to localhost on port `2222`:

```bash
python Honeypot.py
```

To change the bind address or port explicitly:

```bash
HONEYPOT_HOST=127.0.0.1 HONEYPOT_PORT=2222 python Honeypot.py
```

Do not expose this service to the public internet without understanding the network, legal, and data-handling implications. If remote testing is required, use a disposable isolated VM or lab network and set the bind address deliberately.

## Test the fake shell

```bash
ssh -p 2222 test@127.0.0.1
```

The server accepts the connection for observation, rejects password authentication, and provides a limited fake shell only when a session is opened.

## Logging and data handling

Events are written to `honeypot.log` and printed to the console. Authentication telemetry includes the source address, username, and password length; submitted passwords are always redacted and are not persisted.

Example:

```text
[2026-01-01 12:00:00] WARNING - 🔑 AUTH ATTEMPT - IP: 127.0.0.1 | User: test | Password length: 8 | Pass: [REDACTED]
```

The generated `server_rsa.key` and `honeypot.log` contain sensitive lab data. Keep them out of version control and remove them when the experiment is complete.

## Disclaimer

For educational use in an authorized, isolated environment only. Do not collect credentials from systems or users without explicit permission.
