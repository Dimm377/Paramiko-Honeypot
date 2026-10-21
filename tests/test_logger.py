import logging
import pytest
from logger import (
    TelemetryLogger,
    log_connection,
    log_auth_attempt,
    log_command,
    log_disconnect,
    log_error,
    log_info,
    get_telemetry_logger,
)


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_telemetry_logger_in_memory_sink():
    custom_logger = logging.getLogger("TestTelemetryMemory")
    custom_logger.handlers.clear()
    custom_logger.setLevel(logging.INFO)
    handler = ListHandler()
    custom_logger.addHandler(handler)

    telemetry = TelemetryLogger(logger_instance=custom_logger)
    telemetry.log_info("System started")
    telemetry.log_connection("192.168.1.100", 45678)

    assert len(handler.records) == 2
    assert "System started" in handler.records[0].getMessage()
    assert "192.168.1.100:45678" in handler.records[1].getMessage()


def test_auth_attempt_redacts_password():
    custom_logger = logging.getLogger("TestTelemetryAuth")
    custom_logger.handlers.clear()
    custom_logger.setLevel(logging.INFO)
    handler = ListHandler()
    custom_logger.addHandler(handler)

    telemetry = TelemetryLogger(logger_instance=custom_logger)
    telemetry.log_auth_attempt("10.0.0.1", "admin", "supersecret123")

    assert len(handler.records) == 1
    msg = handler.records[0].getMessage()
    assert "admin" in msg
    assert "Password length: 14" in msg
    assert "[REDACTED]" in msg
    assert "supersecret123" not in msg


def test_convenience_functions_work_and_record():
    handler = ListHandler()
    global_logger = get_telemetry_logger().logger
    global_logger.addHandler(handler)

    try:
        log_connection("127.0.0.1", 2222)
        log_command("127.0.0.1", "whoami")
        log_disconnect("127.0.0.1")
        log_error("Test failure")
        log_info("Test notice")

        messages = [r.getMessage() for r in handler.records]
        assert any("CONNECTION - 127.0.0.1:2222" in m for m in messages)
        assert any("COMMAND - IP: 127.0.0.1 | Cmd: whoami" in m for m in messages)
        assert any("DISCONNECT - 127.0.0.1" in m for m in messages)
        assert any("ERROR - Test failure" in m for m in messages)
        assert any("INFO - Test notice" in m for m in messages)
    finally:
        global_logger.removeHandler(handler)
