import socket
import sys
import json
import time

def receive_message(port):
    z=0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', port))
        s.listen()
        print(f"Listening for messages on port {port}")
        
        while(True):
            conn, _ = s.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    message = json.loads(data.decode())
                    current_time = time.time()
                    elapsed_time = current_time - message['start_time']
                    z+=1
                    print(f"Received message: {message['message']}")
                    print(f"Round-trip time: {elapsed_time:.2f} seconds")
                    print(f"Message number {z}")

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print("Usage: python3 client_receive.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    receive_message(port)

