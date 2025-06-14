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
                 
    def handle_file_transfer(self, filename, client_address, data_port):
        try:
            # Create new socket for this file transfer
            transfer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            transfer_socket.bind(('', data_port))
            print(f"Thread started for {filename} on port {data_port}")

            with open(filename, 'rb') as file:
                while True:
                    data, client_addr = transfer_socket.recvfrom(1024)
                    request = data.decode().strip()
                    parts = request.split()

                    if parts[0] == "FILE" and parts[2] == "CLOSE":
                        response = f"FILE {filename} CLOSE_OK"
                        transfer_socket.sendto(response.encode(), client_addr)
                        break

                    if parts[0] == "FILE" and parts[2] == "GET":
                        try:
                            start = int(parts[4])
                            end = int(parts[6])
                            file.seek(start)
                            chunk = file.read(end - start + 1)
                            base64_data = base64.b64encode(chunk).decode()
                            response = f"FILE {filename} OK START {start} END {end} DATA {base64_data}"
                            transfer_socket.sendto(response.encode(), client_addr)
                        except Exception as e:
                            print(f"Error processing file chunk: {e}")
                            continue

            transfer_socket.close()
            print(f"Transfer complete for {filename}")

        except Exception as e:
            print(f"Error in file transfer thread: {e}")