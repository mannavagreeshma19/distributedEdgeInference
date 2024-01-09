import socket
import json
import threading
import time
from node import *
from serviceClass import *

# Configure before startup
MY_IP = "10.0.0.17"
MY_CONTROLER_LISTEN_PORT = 1025
MY_REQUEST_LISTEN = 1027

################# NODE CONTROLLER CONNECTION STUFF #######
node_controllers_lock = threading.Lock()  # Lock for synchronizing access to the node_controllers list

def handle_client_connection(connection, address):
    with connection:
        print(f"Connected by {address}")
        try:
            data = connection.recv(2048)
            if data:
                json_data = json.loads(data.decode('utf-8'))
                handle_node_status(json_data)
        except Exception as e:
           print(f"An error occurred with hjdfakhfla{address}: {e}")
        finally:
            connection.close()
            print(f"Connection with {address} closed.")

def handle_node_status(data):
    status = data.get('status')
    ip = data.get('ip')
    port = data.get('port')
    netList = data.get('netList')
    ram=data.get('ram')
    ramUtilization=data.get('ramUtilization')
    cpu=data.get('cpu')
    cpuUtilization=data.get('cpuUtilization')
    portList=data.get('portList')

    with node_controllers_lock:
        if status == 'up':
            Node(ip, port, cpu, ram, cpuUtilization, ramUtilization, netList, portList) #make sure node does not already exist and isnt just recovering from a crash. 

        elif status == 'update': 
            node=Node.findByIp(ip) #Add error handling if node is not found. 
            node.update(cpuUtilization, ramUtilization, netList, portList)
            print(f"Node controller updated: {ip}:{port}")

def listen_for_connections(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((MY_IP, port))
        server_socket.listen()
        print(f"Server is listening on localhost:{port}")

        while True:
            try:
                connection, address = server_socket.accept()
                client_thread = threading.Thread(target=handle_client_connection, args=(connection, address))
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"An error occurred: {e}")

def start_listener_thread(port):
    listener_thread = threading.Thread(target=listen_for_connections, args=(port,))
    listener_thread.daemon = True
    listener_thread.start()

############ END NODE CONNECTION STUFF #############

############# REQUEST HANDLING STUFF ###############
requests_to_serve = []

def listen_for_requests(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server listening on {host}:{port}")
        
        while True:
            conn, addr = server_socket.accept()
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    try:
                        message = json.loads(data.decode('utf-8'))
                        if all(k in message for k in ('ip', 'port', 'network')):
                            global requests_to_serve
                            requests_to_serve.append((message['ip'], message['port'], message['network']))
                    except json.JSONDecodeError:
                        print("Received non-JSON data")

def start_listen_for_requests_thread():
    listener_thread = threading.Thread(target=listen_for_requests, args=(MY_IP, MY_REQUEST_LISTEN))
    listener_thread.start()

def reply_to_request(entry_ip, entry_port, host, port, network):
    data = {
        'entry_ip': entry_ip,
        'entry_port': entry_port,
        'network': network
    }
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((host, int(port)))
            sock.sendall(json.dumps(data).encode('utf-8'))
            print(f"Sent to {host}:{port} - Entry_IP: {entry_ip}, Network: {network}")
        except ConnectionRefusedError:
            print(f"Connection to {host}:{port} refused. Make sure the server is running.")
        except Exception as e:
            print(f"An error occurred: {e}")

################################################## END REQUEST LOGIC ###########

#must return (entry ip, entry port)
def schedule(request, instances=1, slices=1): #this function belongs in node.py
    n=Node.nodeList[0]
    # netName, startLayer, endLayer, listenPort, nextIP, nextPort, node, child=None, load=None
    s=service("YOLO", 0, None, 5000, "127.0.0.1", 5001, n) 
    n.startService(s)
    return ("127.0.0.1", 5000)


def main_logic():
    while True:
        if len(requests_to_serve) != 0 and len(Node.nodeList) != 0:
            request = requests_to_serve.pop(0)
            run=Node.isRunning(request[2])
            if(run!=False):
                print("Already running")
                reply_to_request(run[0], run[1], request[0], request[1], request[2])#entry_ip, entry_port, host, port, network
            else:
                run=schedule(request)
                reply_to_request(run[0], run[1], request[0], request[1], request[2])
            
        #This is the best place to add crash detection. 
        #for i in nodeList
                #if !i.alive(ttd)
                    #reschedule nets on that node

if __name__ == "__main__":
    start_listener_thread(MY_CONTROLER_LISTEN_PORT)
    start_listen_for_requests_thread()
    main_logic()  # Run the main logic of the master
