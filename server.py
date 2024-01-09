import socket
import json
import sys
import threading
import time
from handwriting import *

def process_message(original_message, start_time, server_id):
    elapsed_time = time.time() - start_time
    original_message += f" - processed by {server_id} in {elapsed_time:.2f} seconds"
    return original_message



def client_handler(conn, addr, is_last, next_server_addr, server_id, control_ip, control_port):
    try:
        data = b""
        while True:
            part = conn.recv(4096)  # Increased buffer size to 4096 for efficiency
            if not part:
                break  # No more data, break the loop
            data += part

        if not data:
            print(f"No data received from {addr}")
            return

        try:
            message = json.loads(data.decode())

            # Perform some processing on the message, e.g., inference
            inferenceResult = predict(model, message['message'])
            message['message'] = inferenceResult

            # Print inference result for debugging
            #print(f"Inference Result: {inferenceResult}")

            # Forwarding the processed message to the next server or returning to the client
            if is_last:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as return_socket:
                    return_socket.connect((message['returnIP'], message['returnPort']))
                    return_socket.sendall(json.dumps(message).encode())
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as forward_socket:
                    forward_socket.connect(next_server_addr)
                    forward_socket.sendall(json.dumps(message).encode())

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {addr}: {e}")
            print(f"Received data: {data.decode()[:1000]}...")  # Print first 1000 characters

    except Exception as e:
        print(f"Server.py Error: Exception handling connection from {addr}: {e}")
    finally:
        conn.close()




def start_server(in_port, is_last, control_ip, control_port,  next_server_ip=None, next_server_port=None):
    server_id = f"Server_{in_port}"
    next_server_addr = (next_server_ip, next_server_port) if next_server_ip else None
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", in_port))
        s.listen()
        print(f"{server_id} listening on port {in_port}")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=client_handler, args=(conn, addr, is_last, next_server_addr, server_id, control_ip, control_port))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    netName = sys.argv[1]
    startLayer = sys.argv[2]
    endLayer = sys.argv[3]
    listenPort = int(sys.argv[4])
    nextIP = None if sys.argv[5] == 'None' else sys.argv[5]
    nextPort = None if sys.argv[6] == 'None' else int(sys.argv[6])

    control_ip = '127.0.0.1'  # Replace with actual control IP
    control_port = 1026  # Replace with actual control port
    is_last= nextPort=='None'

    global model
    model=getModel()
    
    start_server(listenPort, is_last, control_ip, control_port,  nextIP, nextPort)