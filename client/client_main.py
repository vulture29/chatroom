import sys
import socket
import select

HOST = "127.0.0.1"
PORT = 9009
RECV_BUFFER = 4096

def print_prompt():
    sys.stdout.write('[Me] ')
    sys.stdout.flush()

def start_chat_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)

    try:
        sock.connect((HOST, PORT))
    except:
        print "Unable to connect"
        sys.exit()

    print("Connected")
    print_prompt()

    while True:
        socket_list = [sys.stdin, sock]
        ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

        for ready_sock in ready_to_read:
            if ready_sock == sock:
                # from remote msg
                data = sock.recv(RECV_BUFFER)
                if data:
                    sys.stdout.write(data)
                    print_prompt()
                else:
                    print()
                    print("Disconected from server")
            else:
                # from stdin
                msg = sys.stdin.readline()
                sock.send(msg)
                print_prompt()


if __name__ == "__main__":
    start_chat_client()