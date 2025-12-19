import socket
import threading
import paramiko

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', 22))
    server_socket.listen(5)

    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr[0 ]}:{addr[1]}")
    transport = paramiko.Transport(client_socket)
    server_key = paramiko.RSAKey.generate(2048)
    transport.add_server_key(server_key)
    