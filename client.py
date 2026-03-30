from enum import Enum
import socket
import json
import threading
from termcolor import colored, cprint
import os

class pkt_type(int, Enum):
    INFO : int = 1,
    MESSAGE : int = 2,
    SERVERMESSAGE : int = 3,
    SHUTDOWN : int = 4

class cl_cmds(str, Enum):
    CL_DISCONNECT : str = "/dis"

connect_to = "127.0.0.1"
PORT = 55455

connected = False
username = "User"
my_client_id = -1 

lock = threading.Lock()

def connect_to_server(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip,port))
        cprint("Connected", "green")
        
        return s
    except:
        cprint("Failed to connect", "light_red")
        return None

def handle_incoming_data(conn):
    global my_client_id
    global connected
    with conn:
        while connected:
            try:
                received_data = conn.recv(1024)

                if not received_data:
                    with lock:
                        print(colored("Disconnected: ", "yellow") + colored("server disconnect", "white"))
                        conn.close()
                        connected = False
                    break

                pkt_json = json.loads(received_data.decode())
            except (ConnectionAbortedError, OSError):
                break
            except Exception as e:
                cprint(f"{e}", "red")
                break
        
            command = pkt_json["pkt_header"]

            match command:
                case pkt_type.INFO:
                    with lock:
                        my_client_id = pkt_json["c_id"]
                        cprint(f"ID has been assigned to {my_client_id}", "green")
                case pkt_type.MESSAGE:
                    _username = pkt_json["username"]
                    _msg = pkt_json["msg"]
                    print(colored(f"{_username}:", "light_yellow") + f" {_msg}")
                case pkt_type.SERVERMESSAGE:
                    _msg = pkt_json["msg"]
                    cprint(_msg, pkt_json["color"])
                case pkt_type.SHUTDOWN:
                    with lock:
                        connected = False
                    conn.close()
                    os._exit(0)
                case _:
                    print("unknown packet received from server")

sock = connect_to_server(connect_to, PORT)

if sock:
    connected = True

    username = input(colored("Enter a nice username: ", "yellow"))

    with lock:
        sock.sendall(json.dumps(
                {
                    "pkt_header" : pkt_type.INFO, #initial client info
                    "c_id" : my_client_id,
                    "username" : username
                }
            ).encode()
        )

    rcv_thread = threading.Thread(target=handle_incoming_data, args=(sock,))
    rcv_thread.start()

    try:

        while connected:

            msg = input("")

            match msg:
                case cl_cmds.CL_DISCONNECT:
                    sock.close()
                    connected = False
                case _:
                    #regular chat message
                    with lock:
                        send_data = json.dumps({
                            "pkt_header" : pkt_type.MESSAGE, #chat message
                            "c_id" : my_client_id, 
                            "msg" : msg
                        }).encode()

                        sock.sendall(send_data)

    except KeyboardInterrupt:
        sock.close()
        connected = False

