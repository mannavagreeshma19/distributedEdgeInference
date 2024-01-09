# Node Controller Script (control.py)

import socket
import json
import subprocess
import os
import signal
import time
import threading
import psutil



# Configuration variables
MASTER_IP = '10.0.0.17'
MASTER_PORT = 1025
MY_IP = '10.0.0.17'
MY_PORT = 1026
RETRY_LIMIT = 5
RETRY_DELAY = 5  # seconds
cpuCores=24
cpuFreq=5
ram=8
running = {}  # Dictionary to keep track of running processes [message]=pid
                #Above should use netName as key. Return pid



def send_message_to_server(host=MY_IP, master_port=MASTER_PORT):
    """
    Sends a message to the master server with the status, IP, and port of the node controller.
    
    Args:
    status (str): The status of the node controller ('up' or 'update').
    host (str, optional): The hostname of the master server. Defaults to MASTER_IP.
    master_port (int, optional): The port number of the master server. Defaults to MASTER_PORT.
    my_ip (str): The IP of the node controller.
    my_port (int): The port number of the node controller.
    """
    status="up"
    cpuUtilization = psutil.cpu_percent(interval=.5)
    ramUtilization = psutil.virtual_memory().percent
    connections = psutil.net_connections()
    portList = [conn.laddr.port for conn in connections if conn.laddr.port >= 1050]

    
    message = {
        'status': "up",
        'ip': MY_IP,
        'port': MY_PORT,
        'cpu': cpuCores*cpuFreq,
        'ram':ram,
        'cpuUtilization':cpuUtilization,
        'ramUtilization':ramUtilization,
        'netList':[(a, b, d) for (a, b), (_, d) in running.items()],
        'portList':portList
    }
    while(True):
        # Create a socket (SOCK_STREAM means a TCP socket)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
         # Connect to server and send data
            sock.connect((host, master_port))
            sock.sendall(json.dumps(message).encode('utf-8'))
            print(f"Status '{status}' with IP {MY_IP} and port {MY_PORT} sent to {host}:{master_port}")
        cpuUtilization = psutil.cpu_percent(interval=.5)
        ramUtilization = psutil.virtual_memory().percent
        connections = psutil.net_connections()
        portList = [conn.laddr.port for conn in connections if conn.laddr.port >= 1050]
        message = {
        'status': "update",
        'ip': MY_IP,
        'port': MY_PORT,
        'cpu': cpuCores*cpuFreq,
        'ram':ram,
        'cpuUtilization':cpuUtilization,
        'ramUtilization':ramUtilization,
        'netList':[(a, b, d) for (a, b), (_, d) in running.items()],
        'portList':portList
        }
        time.sleep(1)
        

def listen_for_instructions(my_port):
    """Listen for instructions from the master  and from children sending updates."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((MY_IP, MY_PORT))
        server_socket.listen()
        print(f"Listening for instructions on port {my_port}")

        while True:
            print("Ready to accept a new connection.")
            connection, client_address = server_socket.accept()
            with connection:
                print(f"Connected to {client_address}")
                try:
                    while True:
                        data = connection.recv(1024).decode('utf-8')
                        if not data:
                            print("No more data, closing connection.")
                            break
                        instruction = json.loads(data)
                        print(f"Received instruction: {instruction}")
                        handle_instruction(connection, instruction)
                except Exception as e:
                    print(f"An error occurred while handling instructions: {e}")
                finally:
                    print("Closing the connection.")
                    connection.close()

def handle_instruction(connection, instruction):
    """Handle an individual instruction from the master server or worker update."""
    try:
        source=instruction.get('source')
        netName=instruction.get('netName')
        listenPort=instruction.get('listenPort')
        
        if source=='master':
            task = instruction.get('task')
            message = instruction.get('message')
            print(f"Processing task: {task} with message: {message}")
            if task == 'bringup':
              args = message.split()
              proc = subprocess.Popen(['python3', 'server.py'] + args)
              running[(netName,listenPort)] = (proc.pid, time.time())
              print(f"Bringing up {netName} with PID {proc.pid}")

            elif task == 'shutdown':
                pid = running.get((netName, listenPort))[0]
                if pid:
                    os.kill(pid, signal.SIGTERM)
                    del running[(netName,listenPort)]
                    print(f"Shut down {netName} with PID {pid}")
        else:
            #updates are sent by dnn exitnodes everytime they complete a request. These will be used to track time of
            #last request completed. Measured using linux epoch. 
            try:
                print(f"Updating time for exitnode {netName}")
                running[(netName, listenPort)] = (running[(netName, listenPort)][0], time.time())
            except:
                print("Time could not be updated for " + message)     

    except Exception as e:
        print("Error occured in control.py while handling instruction")
        

def main():
    """Main function to set up node controller."""
    t = threading.Thread(target=send_message_to_server, daemon=True)
    t.start()
    #send_message_to_server()
    time.sleep(1)
    listen_for_instructions(MY_PORT)

if __name__ == "__main__":
    main()
