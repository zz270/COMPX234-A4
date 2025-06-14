import socket
import sys
import os
import base64
import time

class UDPClient:
    def __init__(self, server_host, server_port, file_list):
        self.server_host = server_host
        self.server_port = server_port
        self.file_list = file_list
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.initial_timeout = 1000  # 1 second in milliseconds
        self.max_retries = 5

    def send_and_receive(self, message, address, port, timeout=None):
        current_timeout = timeout if timeout else self.initial_timeout
        retries = 0
        
        while retries < self.max_retries:
            try:
                self.socket.settimeout(current_timeout / 1000)
                self.socket.sendto(message.encode(), (address, port))
                response, _ = self.socket.recvfrom(2048)
                return response.decode().strip()
            except socket.timeout:
                retries += 1
                current_timeout *= 2
                print(f"Timeout, retrying ({retries}/{self.max_retries}) with timeout {current_timeout}ms")
                continue
            except Exception as e:
                print(f"Error in send_and_receive: {e}")
                break
        
        raise Exception("Max retries reached, giving up")
    
    def download_file(self, filename):
        try:
            # Request file download
            request = f"DOWNLOAD {filename}"
            response = self.send_and_receive(request, self.server_host, self.server_port)
            
            if response.startswith("ERR"):
                print(f"Error: {response}")
                return False
            
            # Parse OK response
            parts = response.split()
            file_size = int(parts[3])
            data_port = int(parts[5])
            
            print(f"Downloading {filename} (size: {file_size} bytes)")
            
            # Download file chunks
            with open(filename, 'wb') as file:
                bytes_received = 0
                block_size = 1000  # Max bytes per chunk
                
                while bytes_received < file_size:
                    start = bytes_received
                    end = min(start + block_size - 1, file_size - 1)
                    
                    request = f"FILE {filename} GET START {start} END {end}"
                    response = self.send_and_receive(
                        request, self.server_host, data_port,
                        timeout=self.initial_timeout
                    )
                    
                    if not response.startswith(f"FILE {filename} OK"):
                        print(f"Unexpected response: {response}")
                        return False
                    
                    # Parse data response
                    resp_parts = response.split()
                    data_start = int(resp_parts[4])
                    data_end = int(resp_parts[6])
                    data_payload = ' '.join(resp_parts[8:])
                    
                    # Decode and write data
                    chunk = base64.b64decode(data_payload)
                    file.seek(data_start)
                    file.write(chunk)
                    bytes_received += len(chunk)
                    
                    print('*', end='', flush=True)
                
                print()  # New line after progress stars
                
                # Close connection
                request = f"FILE {filename} CLOSE"
                response = self.send_and_receive(request, self.server_host, data_port)
                
                if response != f"FILE {filename} CLOSE_OK":
                    print(f"Unexpected close response: {response}")
                    return False
                
            print(f"Successfully downloaded {filename}")
            return True
            
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return False

def start(self):
        try:
            with open(self.file_list, 'r') as f:
                files = [line.strip() for line in f if line.strip()]
            
            for filename in files:
                self.download_file(filename)
                
        except FileNotFoundError:
            print(f"Error: File list '{self.file_list}' not found")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.socket.close()