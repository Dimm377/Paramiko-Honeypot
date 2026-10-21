# Paramiko Honeypot Architecture & Security Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor Paramiko Honeypot to eliminate architectural friction, fix the unreachable shell bug, harden against DoS and resource leaks, and establish a deep-module test suite.

**Architecture:** Decompose the honeypot into deep modules behind clean seams: a configurable `TelemetryLogger` without import-time side effects, a resilient `TerminalStream` parser for interactive sessions, a unified `HoneypotSession` managing transport and auth lifecycle, and a bounded `HoneypotServer` daemon with in-memory host key caching.

**Tech Stack:** Python 3.9+, Paramiko, pytest.

**Spec:** Current codebase review and architectural audit (`/tmp/architecture-review-20261021-165900.html`).

## Global Constraints
- Must remain compatible with Python 3.9 through 3.12.
- Preserve backward-compatible entrypoints (`python Honeypot.py`) and environment variables (`HONEYPOT_HOST`, `HONEYPOT_PORT`).
- Default bind address must remain safe (`127.0.0.1`).
- Passwords must remain redacted by default in logs (`[REDACTED]`).
- All tests must pass via `pytest tests/`.

## Review Focus
1. Multi-byte chunks in `channel.recv()` — pasted commands and bot scripts must be parsed without stalling or breaking line execution.
2. Authentication mode switch — `HONEYPOT_AUTH_MODE=accept_all` must allow SSH clients to proceed to the shell channel, while `reject_all` rejects auth.
3. Transport resource cleanup — all exceptions during handshake or shell session must ensure `transport.close()` and `socket.close()` are called without leaking threads.
4. Non-interactive `exec` command execution — `ssh -p 2222 user@host "id"` must return fake output and close gracefully rather than hanging.
5. Concurrency bounds — connection spikes must be handled via a bounded worker pool rather than unbounded thread creation.

---

### Task 1: Deep Telemetry Logger Module

**Files:**
- Modify: `logger.py`
- Test: `tests/test_logger.py`

- [ ] **Step 1:** Write failing tests in `tests/test_logger.py` for `TelemetryLogger` class and convenience functions:
  - Test structured event emission.
  - Test password redaction.
  - Test custom/in-memory sink without disk side-effects.
  - Test backward-compatible functions (`log_connection`, `log_auth_attempt`, `log_command`, `log_disconnect`, `log_error`, `log_info`).
- [ ] **Step 2:** Run `pytest tests/test_logger.py` to confirm failure (RED).
- [ ] **Step 3:** Implement `TelemetryLogger` in `logger.py` with clean configuration and lazy file handler initialization.
- [ ] **Step 4:** Run `pytest tests/test_logger.py` to confirm all pass (GREEN).
- [ ] **Step 5:** Commit changes.

---

### Task 2: Resilient Terminal Stream Parser & Command Dispatcher

**Files:**
- Modify: `ssh_server.py`
- Test: `tests/test_terminal.py`

- [ ] **Step 1:** Write failing tests in `tests/test_terminal.py` for `TerminalStream` and `CommandDispatcher`:
  - Test chunked/multi-byte input parsing (e.g. `b"uname -a\r\n"`).
  - Test line feed normalization (`\r`, `\n`, `\r\n`).
  - Test backspace handling (`\x7f`, `\b`).
  - Test control characters (Ctrl+C `\x03`, Ctrl+D `\x04`).
  - Test command dispatching for known commands (`ls`, `whoami`, `id`, `pwd`, etc.) and unknown commands.
- [ ] **Step 2:** Run `pytest tests/test_terminal.py` to confirm failure (RED).
- [ ] **Step 3:** Implement `TerminalStream` and `CommandDispatcher` in `ssh_server.py`.
- [ ] **Step 4:** Run `pytest tests/test_terminal.py` to confirm all pass (GREEN).
- [ ] **Step 5:** Commit changes.

---

### Task 3: Configurable Auth Policy & Deep HoneypotSession

**Files:**
- Modify: `ssh_server.py`
- Modify: `Honeypot.py`
- Test: `tests/test_session.py`

- [ ] **Step 1:** Write failing tests in `tests/test_session.py`:
  - Test `SSHServerInterface` in `accept_all` mode returns `AUTH_SUCCESSFUL`.
  - Test `SSHServerInterface` in `reject_all` mode returns `AUTH_FAILED`.
  - Test `check_channel_exec_request` executes command and writes response to channel with exit status.
  - Test `HoneypotSession.handle()` cleans up socket and transport resources in `finally`.
- [ ] **Step 2:** Run `pytest tests/test_session.py` to confirm failure (RED).
- [ ] **Step 3:** Implement `HoneypotSession` and update `SSHServerInterface` / `FakeShell` in `ssh_server.py`.
- [ ] **Step 4:** Run `pytest tests/test_session.py` to confirm all pass (GREEN).
- [ ] **Step 5:** Commit changes.

---

### Task 4: Server Daemon Lifecycle, Host Key Caching & Concurrency Hardening

**Files:**
- Modify: `Honeypot.py`
- Test: `tests/test_server_daemon.py`

- [ ] **Step 1:** Write failing tests in `tests/test_server_daemon.py`:
  - Test host key caching (key is generated or loaded once, not on every connection).
  - Test `HoneypotServer` initialization with host, port, max_workers.
  - Test graceful shutdown behavior.
- [ ] **Step 2:** Run `pytest tests/test_server_daemon.py` to confirm failure (RED).
- [ ] **Step 3:** Implement `HoneypotServer` in `Honeypot.py` using `ThreadPoolExecutor` and cached RSA key.
- [ ] **Step 4:** Run `pytest tests/test_server_daemon.py` to confirm all pass (GREEN).
- [ ] **Step 5:** Commit changes.

---

### Task 5: Documentation & CI Integration

**Files:**
- Modify: `README.md`
- Modify: `requirements.txt`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1:** Add `pytest` to `requirements.txt` (or dev dependencies section).
- [ ] **Step 2:** Update `.github/workflows/ci.yml` to run `pytest tests/ -v`.
- [ ] **Step 3:** Update `README.md` with documentation on `HONEYPOT_AUTH_MODE`, running tests, and architecture.
- [ ] **Step 4:** Run full test suite `pytest tests/ -v` and syntax compilation.
- [ ] **Step 5:** Commit changes.
