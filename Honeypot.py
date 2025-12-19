#!/usr/bin/env python3
import socket
import threading
import paramiko
import os

from ssh_server import SSHServerInterface, FakeShell
from logger import log_connection, log_disconnect, log_error, log_info

HOST = ""
PORT = 2222
RSA_KEY_FILE = "server_rsa.key"

def generate_rsa_key():
    if not os.path.exists(RSA_KEY_FILE):
        log_info(f"Generating RSA key: {RSA_KEY_FILE}")
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(RSA_KEY_FILE)
        log_info("RSA key generated successfully")
    return paramiko.RSAKey.from_private_key_file(RSA_KEY_FILE)

def handle_connection(client_socket: socket.socket, client_addr: tuple):
    client_ip = client_addr[0]
    client_port = client_addr[1]
    
    log_connection(client_ip, client_port)
    
    try:
        transport = paramiko.Transport(client_socket)
        transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.4"
        
        server_key = generate_rsa_key()
        transport.add_server_key(server_key)
        
        ssh_interface = SSHServerInterface(client_ip)
        transport.start_server(server=ssh_interface)
        
        channel = transport.accept(timeout=30)
        
        if channel is None:
            log_error(f"No channel from {client_ip}")
            transport.close()
            return
        
        ssh_interface.event.wait(timeout=10)
        
        if ssh_interface.event.is_set():
            fake_shell = FakeShell(channel, client_ip)
            fake_shell.handle()
        
        channel.close()
        
    except paramiko.SSHException as e:
        log_error(f"SSH error from {client_ip}: {e}")
    except Exception as e:
        log_error(f"Error handling {client_ip}: {e}")
    finally:
        log_disconnect(client_ip)
        client_socket.close()

def main():
    generate_rsa_key()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(100)
        
        log_info(f"🍯 SSH Honeypot started on port {PORT}")
        log_info("Press Ctrl+C to stop")
        
        while True:
            try:
                client_socket, client_addr = server_socket.accept()
                thread = threading.Thread(target=handle_connection, args=(client_socket, client_addr), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                break
                
    except PermissionError:
        log_error(f"Permission denied for port {PORT}. Try port > 1024 or run as root.")
    except OSError as e:
        log_error(f"Socket error: {e}")
    finally:
        log_info("Shutting down honeypot...")
        server_socket.close()

if __name__ == "__main__":
    main()