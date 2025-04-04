import socket
import threading
import sys

def receive_messages(sock):
    """
    A thread that continuously listens for messages
    from the server socket and prints them out.
    """
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from server.")
                break
            print(data.decode(), end="")
        except ConnectionResetError:
            print("Connection forcibly closed by server.")
            break
        except:
            # Generic catch: could be triggered by forced closure
            break

    # If we reach here, the receiving thread ends
    sock.close()
    sys.exit()

def start_client(server_ip="127.0.0.1", server_port=12345):
    """
    Connect to the server, start a thread for receiving messages,
    and then read user input to send messages to the server.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, server_port))
        print(f"Connected to server {server_ip}:{server_port}")
    except Exception as e:
        print(f"Could not connect to server {server_ip}:{server_port}: {e}")
        return

    # Start a background thread to listen for messages from server
    receiver_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver_thread.start()

    # Main loop: read input from the user and send to server
    try:
        while True:
            msg = input()
            if not msg:
                # If user just pressed Enter, skip
                continue

            # Send the message to the server
            sock.sendall((msg + "\n").encode())

            if msg == "/quit":
                # Let the server handle disconnection
                break

    except KeyboardInterrupt:
        print("\nYou interrupted the client. Disconnecting.")
        sock.sendall("/quit\n".encode())
    finally:
        sock.close()
        sys.exit()

if __name__ == "__main__":
    # To run the client: python client.py [SERVER_IP] [SERVER_PORT]
    if len(sys.argv) >= 3:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        server_ip = sys.argv[1]
        server_port = 12345
    else:
        server_ip = "192.168.1.103"
        server_port = 12345

    start_client(server_ip, server_port)
