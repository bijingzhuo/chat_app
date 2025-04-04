import socket
import threading

clients = {}
channels = {}
lock = threading.Lock()

def broadcast_channel_message(sender_nick, channel_name, message):
    """
    Send 'message' to all clients in 'channel_name', coming from 'sender_nick'.
    """
    with lock:
        if channel_name not in channels:
            return  # Channel doesn't exist or no one is in it

        for nickname in channels[channel_name]:
            if nickname in clients and nickname != sender_nick:
                try:
                    clients[nickname].sendall(f"[Channel {channel_name}] {sender_nick}: {message}\n".encode())
                except:
                    # If sending fails, we ignore or remove the client
                    pass

def private_message(sender_nick, target_nick, message):
    """
    Send a private message to 'target_nick' from 'sender_nick'.
    """
    with lock:
        if target_nick not in clients:
            # Let sender know the target does not exist
            if sender_nick in clients:
                clients[sender_nick].sendall(f"User '{target_nick}' not found.\n".encode())
            return

        try:
            clients[target_nick].sendall(f"[Private] {sender_nick}: {message}\n".encode())
        except:
            pass

def handle_client_connection(client_socket, client_address):
    """
    Thread target for handling each client connection:
    - Reads commands/messages from the client.
    - Updates global structures accordingly.
    - Forwards messages to the appropriate recipients.
    """
    nickname = None

    # Send a welcome message
    client_socket.sendall("Welcome to the chat server!\n".encode())
    client_socket.sendall("Use '/nick <yourNickname>' to set your nickname.\n".encode())
    client_socket.sendall("Use '/join <channel>' to join a channel.\n".encode())
    client_socket.sendall("Use '/send <channel> <message>' to send a message to a channel.\n".encode())
    client_socket.sendall("Use '/pm <nick> <message>' to send a private message.\n".encode())
    client_socket.sendall("Use '/quit' to disconnect.\n\n".encode())

    while True:
        try:
            data = client_socket.recv(1024)
        except ConnectionResetError:
            # Client disconnected unexpectedly
            data = None

        if not data:
            # This means client has disconnected
            break

        message = data.decode().strip()
        if not message:
            continue  # Empty line, just ignore

        # Command parsing
        if message.startswith("/nick "):
            # /nick <name>
            desired_nick = message.split(" ", 1)[1].strip()
            if not desired_nick:
                client_socket.sendall("Nickname cannot be empty.\n".encode())
                continue

            with lock:
                if desired_nick in clients:
                    client_socket.sendall("Nickname already taken. Try another one.\n".encode())
                else:
                    # Remove old nickname from data structures if it existed
                    if nickname and nickname in clients:
                        del clients[nickname]
                        # Also remove from all channels
                        for ch in channels.values():
                            if nickname in ch:
                                ch.remove(nickname)

                    # Set new nickname
                    nickname = desired_nick
                    clients[nickname] = client_socket
                    client_socket.sendall(f"Nickname set to '{nickname}'.\n".encode())

        elif message.startswith("/join "):
            # /join <channel>
            channel_name = message.split(" ", 1)[1].strip()
            if not channel_name:
                client_socket.sendall("Channel name cannot be empty.\n".encode())
                continue

            if not nickname:
                client_socket.sendall("You must set a nickname before joining channels.\n".encode())
                continue

            with lock:
                if channel_name not in channels:
                    channels[channel_name] = set()
                channels[channel_name].add(nickname)

            client_socket.sendall(f"You have joined channel '{channel_name}'.\n".encode())

        elif message.startswith("/send "):
            # /send <channel> <message>
            parts = message.split(" ", 2)
            if len(parts) < 3:
                client_socket.sendall("Usage: /send <channel> <message>\n".encode())
                continue

            channel_name, msg = parts[1], parts[2]
            if not nickname:
                client_socket.sendall("You must set a nickname before sending messages.\n".encode())
                continue

            with lock:
                if channel_name not in channels or nickname not in channels[channel_name]:
                    client_socket.sendall(f"You must join channel '{channel_name}' before sending messages there.\n".encode())
                    continue

            # Broadcast this message to the channel
            broadcast_channel_message(nickname, channel_name, msg)

        elif message.startswith("/pm "):
            # /pm <targetNick> <message>
            parts = message.split(" ", 2)
            if len(parts) < 3:
                client_socket.sendall("Usage: /pm <nick> <message>\n".encode())
                continue

            target_nick, msg = parts[1], parts[2]
            if not nickname:
                client_socket.sendall("You must set a nickname before sending private messages.\n".encode())
                continue

            private_message(nickname, target_nick, msg)

        elif message == "/quit":
            client_socket.sendall("Disconnecting...\n".encode())
            break

        else:
            # Unknown command or direct text. 
            # You could handle raw chat messages here if you want them to go to a default channel.
            client_socket.sendall("Unknown command. Try /nick, /join, /send, /pm, or /quit.\n".encode())

    # If we reach here, the client is disconnecting
    with lock:
        if nickname and nickname in clients:
            del clients[nickname]
            # Remove from all channels
            for ch in channels.values():
                if nickname in ch:
                    ch.remove(nickname)

    client_socket.close()
    print(f"Client disconnected: {client_address}")

def start_server(host="0.0.0.0", port=12345):
    """
    Starts the TCP server on the specified host and port,
    and listens indefinitely for client connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # up to 5 pending connections
    print(f"Server listening on {host}:{port} ...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            thread = threading.Thread(
                target=handle_client_connection,
                args=(client_socket, client_address),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # To run the server, do: python server.py [PORT]
    import sys

    if len(sys.argv) >= 2:
        port = int(sys.argv[1])
    else:
        port = 12345 

    start_server(port=port)
