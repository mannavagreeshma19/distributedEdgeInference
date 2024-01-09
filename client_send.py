from io import BytesIO
import socket
import json
import time
import base64
from PIL import Image
MY_IP="10.0.0.17"
MY_PORT=1028

MASTER_IP="10.0.0.17"
MASTER_PORT=1027


def encode_image_to_base64(image_path):
    with Image.open(image_path) as image:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()

def send_message(server_ip, server_port, return_ip, return_port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        start_time = time.time()
        message_payload = {
            "message": message,
            "returnIP": return_ip,
            "returnPort": return_port,
            "start_time": start_time
        }
        encoded_payload = json.dumps(message_payload).encode()
        s.sendall(encoded_payload)




if __name__ == "__main__":

    data=("127.0.0.1", 5000) #temporarily hardcoded entry point for testing. remove line
    server_ip = data[0]
    server_port = data[1]
    return_ip = MY_IP
    return_port = 5002

    #Images encoded to be sent to dnn in json.
    encodedImage1=encode_image_to_base64("testImage.jpg")
    encodeImage2=encode_image_to_base64("testImage2.jpg")

    # read arrival times json
    file_path="bursty_arrival_times.json"
    with open(file_path, 'r') as file:
        json_data = json.load(file)

    # Re-creating the dictionary to map keys to their respective values
    keys = list(json_data.keys())
    values_dict = {key: json_data[key] for key in keys}
    
    for k in keys:
        print(values_dict[k][0][0])


    start_time=time.time()
    # send messages to server based on arrival times
    while(True):

        next=float("inf")
        model=None
        for a in keys: # iterate through each model
            if(next>values_dict[a][0][0]):
                next=values_dict[a][0][0]
                model=a
        if model!=None:
            values_dict[model][0].pop(0)

        current_time=time.time()
        if(current_time-start_time<next):
            time.sleep(next-(current_time-start_time))

        #server is the server running the dnn you are wnating to do inference on. 
        #format(server1 ip, server 1 port, final destination ip, final destination port, image to do inference on)
        send_message(server_ip, server_port, "10.0.0.17", 5002, encodedImage1) #you will need to change port and 
                                                                                    #ip to match model you are using.
        
