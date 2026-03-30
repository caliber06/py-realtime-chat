from enum import Enum
import socket
import json
import threading
import itertools
from termcolor import colored, cprint
import time
import os

class pkt_type(int, Enum):
    INFO : int = 1,
    MESSAGE : int = 2,
    SERVERMESSAGE : int = 3,
    SHUTDOWN : int = 4

IP = "127.0.0.1"
PORT = 55455

next_client_id = itertools.count(start=1)
connected_clients = {

}
lock = threading.Lock()

kill = threading.Event()

def handle_client(conn, addr, c_id):
    with conn:
        cprint(f"{addr} connected.", "green")
        while True:

            try:
                received_data = conn.recv(1024).decode()
                
                if not received_data:
                    break

                pkt_json = json.loads(received_data)
            except (ConnectionResetError, OSError):
                
                break
            except Exception as e:
                cprint(f"error with {addr}: {e}", "red")
                break
            
            
            #data handling
            command = pkt_json["pkt_header"]

            match command:
                case pkt_type.INFO:
                    _un = pkt_json["username"]

                    with lock:
                        connected_clients[c_id] = {
                            "socket" : conn,
                            "address" : addr,
                            "username" : _un,
                        }

                        #relay client their ID
                        send_data = json.dumps(
                            {
                                "pkt_header" : pkt_type.INFO,
                                "c_id" : c_id
                            }
                        ).encode()
                        conn.sendall(send_data)

                        time.sleep(0.01)
                        
                        #broadcast connection message to all clients
                        broadcast_message(f"--{_un} has entered the chat--")
                        
                        cprint(f"Setting {_un} id to {c_id}", "grey")

                case pkt_type.MESSAGE:
                    _id = pkt_json["c_id"]
                    _msg = pkt_json["msg"]
                    cprint(f"{connected_clients[_id]["username"]} (user id {_id}) says: {_msg}", "grey")

                    relay_messages(_id, _msg)

                    
                    
                case _:
                    print("unknown command")

            if not pkt_json:
                break
            
            
    #handle disconnect
    
    with lock:
        _un = connected_clients[c_id]["username"]

        connected_clients.pop(c_id, None)

        cprint(f"{addr} disconnected", "yellow")

        broadcast_message(f"--{_un} has left the chat--")

        
    conn.close()
        

    #this thread is freed when this function ends.

def relay_messages(id, msg):
    for cl in connected_clients.keys():
        if not cl == id:
            connected_clients[cl]["socket"].sendall(
                json.dumps({
                    "pkt_header" : pkt_type.MESSAGE,
                    "username" : connected_clients[id]["username"],
                    "msg" : msg,
                }).encode()
            )

def broadcast_message(msg, color="yellow"):
    for cl in connected_clients.keys():
        connected_clients[cl]["socket"].sendall(
            json.dumps({
                "pkt_header" : pkt_type.SERVERMESSAGE,
                "msg" : msg,
                "color" : color
            }).encode()
        )

def shutdown():
    broadcast_message("Server shutting down", "red")
    with lock:
        for cl in connected_clients.keys():
            connected_clients[cl]["socket"].sendall(
                json.dumps({
                    "pkt_header" : pkt_type.SHUTDOWN,
                }).encode()
            )
            time.sleep(1)
            connected_clients[cl]["socket"].close()
            print(f"Closing connection #{cl}")
 
def server_commands():
    try:
        while not kill.is_set():
            cmd = input("")

            if cmd == "/quit" or cmd == "/kill":
                kill.set()
                shutdown()
                cprint("Server closed.", "yellow")
                os._exit(0)
                break

    except EOFError:
        cprint("Use /kill or /quit to shut down the server.", "light_red")
    finally:
        command_thread = threading.Thread(target=server_commands)
        command_thread.daemon = True
        command_thread.start()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((IP, PORT))
    sock.listen()
    
    cprint("Server listening", "green")

    while not kill.is_set():
        command_thread = threading.Thread(target=server_commands)
        command_thread.daemon = True
        command_thread.start()

        connection, address = sock.accept()

        #create new thread for new client
        client_thread = threading.Thread(target=handle_client, args=(connection, address, next(next_client_id)))
        client_thread.start()
        

