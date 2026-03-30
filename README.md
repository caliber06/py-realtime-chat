# py-realtime-chat
A simple console client-server chat app written in python. 

# About
This is a personal project written in python, pulling in the following libraries:
- socket
- json (for structuring packets)
- threading
- itertools (thread safe incrementing for managing client IDs)
- time
- os
- enum
- termcolor (for console styling/coloring)

# How to run
- cd to the project directory and run `py server.py`
- In another instance run `py client.py`, and the client will attempt to connect to the server.
- The default IP is `localhost` or `127.0.0.1`. You can change that by simply editing the `connect_to` variable in `client.py` to another IPv4 address.

# How to use
- You can use /kill or /quit to end the server process
- /dis to disconnect on the clientside.

# Takeaways
I wrote this as a personal portfolio project and to learn python and basic networking principles that aren't handled in some kind of framework like I'm used to in game engines (godot)

I learned more about threading which in the past I have had limited exposure to. Upon each connection, the server creates a new thread to listen for incoming data from said client.

# Possible future additions
- GUI
- Channels (like Discord or IRC)
