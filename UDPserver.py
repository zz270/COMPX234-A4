import socket
import threading
import random
import os
import base64
class UDPServer:
    def __init__(self, port):
        self.server_port = port
        self.welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.welcome_socket.bind(('', self.server_port))
        print(f"Server started on port {self.server_port}")

    def start(self):
        while True:
            try:
                data, client_address = self.welcome_socket.recvfrom(1024)
                client_request = data.decode().strip()
                print(f"Received from {client_address}: {client_request}")

                parts = client_request.split()
                if len(parts) < 2 or parts[0] != "DOWNLOAD":
                    continue

                filename = parts[1]
                if not os.path.exists(filename):
                    response = f"ERR {filename} NOT_FOUND"
                    self.welcome_socket.sendto(response.encode(), client_address)
                    continue

                file_size = os.path.getsize(filename)
                data_port = random.randint(50000, 51000)
                response = f"OK {filename} SIZE {file_size} PORT {data_port}"
                self.welcome_socket.sendto(response.encode(), client_address)

                # Start new thread to handle file transfer
                threading.Thread(
                    target=self.handle_file_transfer,
                    args=(filename, client_address, data_port)
                ).start()

            except Exception as e:
                print(f"Error in main server loop: {e}")
                 