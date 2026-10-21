import socket
import threading
from typing import List, Tuple, Optional
import paramiko
from paramiko import AUTH_FAILED, AUTH_SUCCESSFUL, OPEN_SUCCEEDED

from logger import log_auth_attempt, log_command, log_error, log_info


class StreamEvent:
    def __init__(self, kind: str, value: str = ""):
        self.kind = kind
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, StreamEvent):
            return False
        return self.kind == other.kind and self.value == other.value

    def __repr__(self):
        return f"StreamEvent({self.kind!r}, {self.value!r})"


class TerminalStream:
    """Parses raw terminal bytes into high-level stream events (commands, interrupts, echoes)."""

    def __init__(self):
        self.current_line: str = ""
        self._in_escape: bool = False
        self._escape_seq: str = ""
        self._last_was_cr: bool = False

    def feed(self, data: bytes) -> List[StreamEvent]:
        events: List[StreamEvent] = []
        text = data.decode("utf-8", errors="ignore")

        for char in text:
            # Handle ANSI escape sequence state machine
            if self._in_escape:
                self._escape_seq += char
                # CSI sequences terminate on characters between 0x40 and 0x7E
                if len(self._escape_seq) > 1 and char.isalpha() or char in ("~", "@"):
                    self._in_escape = False
                    self._escape_seq = ""
                continue

            if char == "\x1b":
                self._in_escape = True
                self._escape_seq = "\x1b"
                continue

            if char == "\x03":  # Ctrl+C
                self.current_line = ""
                self._last_was_cr = False
                events.append(StreamEvent("INTERRUPT", "^C"))
                continue

            if char == "\x04":  # Ctrl+D / EOF
                events.append(StreamEvent("EOF"))
                continue

            if char in ("\x7f", "\b"):  # Backspace
                if self.current_line:
                    self.current_line = self.current_line[:-1]
                    events.append(StreamEvent("BACKSPACE", "\b \b"))
                self._last_was_cr = False
                continue

            if char == "\r":
                self._last_was_cr = True
                events.append(StreamEvent("COMMAND", self.current_line.strip()))
                self.current_line = ""
                continue

            if char == "\n":
                if self._last_was_cr:
                    # Ignore \n immediately following \r (CRLF pair)
                    self._last_was_cr = False
                    continue
                self._last_was_cr = False
                events.append(StreamEvent("COMMAND", self.current_line.strip()))
                self.current_line = ""
                continue

            self._last_was_cr = False
            self.current_line += char
            events.append(StreamEvent("ECHO", char))

        return events


class CommandDispatcher:
    """Evaluates simulated bash commands for the fake honeypot environment."""

    def __init__(self, hostname: str = "ubuntu-server", username: str = "root"):
        self.hostname = hostname
        self.username = username

    def execute(self, command_line: str) -> Tuple[str, bool]:
        """Returns (response_text, should_exit)"""
        clean_cmd = command_line.strip()
        if not clean_cmd:
            return ("", False)

        parts = clean_cmd.split()
        cmd = parts[0]

        if cmd in ("exit", "logout"):
            return ("", True)

        fake_responses = {
            "ls": "Desktop  Documents  Downloads  Music  Pictures  Videos",
            "pwd": "/root",
            "whoami": self.username,
            "id": f"uid=0({self.username}) gid=0({self.username}) groups=0({self.username})",
            "uname": "Linux",
            "hostname": self.hostname,
            "cat": "cat: No such file or directory",
            "cd": "",
        }

        response = fake_responses.get(cmd, f"{cmd}: command not found")
        return (response, False)

    def dispatch(self, command_line: str) -> str:
        res, _ = self.execute(command_line)
        return res


class SSHServerInterface(paramiko.ServerInterface):
    """Paramiko server callback interface handling channel, auth, and exec requests."""

    def __init__(self, client_ip: str, auth_mode: str = "accept_all"):
        self.client_ip = client_ip
        self.auth_mode = auth_mode
        self.event = threading.Event()
        self.dispatcher = CommandDispatcher()

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username: str, password: str) -> int:
        log_auth_attempt(self.client_ip, username, password)
        if self.auth_mode == "accept_all":
            return AUTH_SUCCESSFUL
        return AUTH_FAILED

    def check_auth_publickey(self, username: str, key) -> int:
        return AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "password"

    def check_channel_shell_request(self, channel) -> bool:
        self.event.set()
        return True

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ) -> bool:
        return True

    def check_channel_exec_request(self, channel, command: bytes) -> bool:
        cmd = command.decode("utf-8", errors="ignore").strip()
        log_command(self.client_ip, cmd)

        # Non-interactive command execution (e.g. automated scanners or ssh host "cmd")
        response, _ = self.dispatcher.execute(cmd)
        if response:
            channel.send(f"{response}\r\n")
        channel.send_exit_status(0)
        channel.close()
        return True


class FakeShell:
    """Simulated interactive shell session with realistic prompt and command feedback."""

    def __init__(self, channel, client_ip: str, hostname: str = "ubuntu-server"):
        self.channel = channel
        self.client_ip = client_ip
        self.hostname = hostname
        self.username = "root"
        self.dispatcher = CommandDispatcher(hostname=self.hostname, username=self.username)
        self.stream = TerminalStream()

    def get_prompt(self) -> str:
        return f"{self.username}@{self.hostname}:~$ "

    def handle(self):
        try:
            self.channel.settimeout(60.0)  # 60s idle timeout
            self.channel.send("\r\nWelcome to Ubuntu 22.04.3 LTS\r\n\r\n")
            self.channel.send(self.get_prompt())

            while True:
                data = self.channel.recv(1024)
                if not data:
                    break

                events = self.stream.feed(data)
                for event in events:
                    if event.kind == "COMMAND":
                        cmd = event.value
                        if cmd:
                            log_command(self.client_ip, cmd)
                            response, should_exit = self.dispatcher.execute(cmd)
                            if response:
                                self.channel.send(f"\r\n{response}")
                            if should_exit:
                                return
                        self.channel.send(f"\r\n{self.get_prompt()}")
                    elif event.kind == "ECHO":
                        self.channel.send(event.value)
                    elif event.kind == "BACKSPACE":
                        self.channel.send("\b \b")
                    elif event.kind == "INTERRUPT":
                        self.channel.send("^C\r\n" + self.get_prompt())
                    elif event.kind == "EOF":
                        return
        except (socket.timeout, EOFError, OSError):
            pass
        except Exception as e:
            log_error(f"Error in fake shell for {self.client_ip}: {e}")
        finally:
            try:
                self.channel.close()
            except Exception:
                pass

    def execute_fake_command(self, command: str) -> str:
        return self.dispatcher.dispatch(command)
