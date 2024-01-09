Overview:
This system distributes network inference over edge devices to achieve better performance on bursty 
workloads through pipeline like model parallelism. 

Components:
master.py:
    This service is responsible for tracking which nodes are up aswell as what they are running. 
    This service recieved up messages and utilization messages from controler.py

    This service recieves messages from clients and responds with a network endpoint to send inference requests to.
        Listen Ports:
            Port 1025 listens for controler messages:
                JSON Format-
            Port 1027 listens for requests from drones/clients/wlg:
                JSON Format-
        

controler.py:
    This service runs on each node and is responsible for bringing up and shutting down inference servers. 
        Listen Port:
            Port 1026 listens for bringup or shutdown requests from master.
            JSON Format-

server.py:
    This service accepts an inference request, performs partial inference, and forwards to next node. 
        In Ports:
            Listen prot determined at startup.
            JSON Format-

WLG:
    (This is currently broken into client_recieve.py and client_send.py)
    This service sends fake requests to master then sends inference request to provided entry point.

StartUp Process:
    Start master first
    1)python3 master.py
    Start controler. 
    2)python3 controler.py
    start wlg: start recieve then send.
    3)python3 client_recieve.py <inPort>
    4)python3 client_recieve.py

Requirments:
    python 3.10
    sudo apt install python3-psutil
    pytorch
    The ability so ssh into existing system.

To-Do:
    Add actual inference to server.py rather than just delayed message passing. 
    Add better bringup/shutdown logic to master
    Add an aditional field that quantifies performance to the controlers output so the master can use it in scheduling.
    Integrate new bursty wlg. 

Note:
    Sending messages to external networks is going to be hard without enabling port forwarding on router. Find workaround. Reverse Shell type approach. VPN. 