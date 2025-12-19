import paramiko
from paramiko import AUTH_FAILED, AUTH_SUCCESSFUL, OPEN_SUCCEEDED
import threading
from logger import log_auth_attempt, log_command, log_info

class SSHServerInterface(paramiko.ServerInterface):
    
    def __init__(self, client_ip: str):
        self.client_ip = client_ip
        self.event = threading.Event()
    
    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username: str, password: str) -> int:
        log_auth_attempt(self.client_ip, username, password)
        return AUTH_FAILED
    
    def check_auth_publickey(self, username: str, key) -> int:
        return AUTH_FAILED
    
    def get_allowed_auths(self, username: str) -> str:
        return "password"
    
    def check_channel_shell_request(self, channel) -> bool:
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes) -> bool:
        return True
    
    def check_channel_exec_request(self, channel, command: bytes) -> bool:
        cmd = command.decode("utf-8", errors="ignore")
        log_command(self.client_ip, cmd)
        return True


class FakeShell:
    
    def __init__(self, channel, client_ip: str):
        self.channel = channel
        self.client_ip = client_ip
        self.hostname = "ubuntu-server"
        self.username = "root"
    
    def get_prompt(self) -> str:
        return f"{self.username}@{self.hostname}:~$ "
    
    def handle(self):
        try:
            self.channel.send(f"\r\nWelcome to Ubuntu 22.04.3 LTS\r\n\r\n")
            self.channel.send(self.get_prompt())
            
            command_buffer = ""
            while True:
                data = self.channel.recv(1024)
                if not data:
                    break
                
                char = data.decode("utf-8", errors="ignore")
                
                if char in ("\r", "\n"):
                    if command_buffer.strip():
                        log_command(self.client_ip, command_buffer.strip())
                        response = self.execute_fake_command(command_buffer.strip())
                        self.channel.send(f"\r\n{response}")
                    self.channel.send(f"\r\n{self.get_prompt()}")
                    command_buffer = ""
                elif char == "\x7f":
                    if command_buffer:
                        command_buffer = command_buffer[:-1]
                        self.channel.send("\b \b")
                elif char == "\x03":
                    self.channel.send("^C\r\n" + self.get_prompt())
                    command_buffer = ""
                elif char == "\x04":
                    break
                else:
                    command_buffer += char
                    self.channel.send(char)
        except Exception:
            pass
        finally:
            self.channel.close()
    
    def execute_fake_command(self, command: str) -> str:
        cmd = command.split()[0] if command else ""
        
        fake_responses = {
            "ls": "Desktop  Documents  Downloads  Music  Pictures  Videos",
            "pwd": "/root",
            "whoami": "root",
            "id": "uid=0(root) gid=0(root) groups=0(root)",
            "uname": "Linux",
            "hostname": self.hostname,
            "cat": "cat: No such file or directory",
            "cd": "",
            "exit": "",
            "logout": "",
        }
        
        if cmd in ("exit", "logout"):
            self.channel.close()
            return ""
        
        return fake_responses.get(cmd, f"{cmd}: command not found")
