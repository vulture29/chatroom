import sys
import socket
import select

HOST = "127.0.0.1"
PORT = 9009
RECV_BUFFER = 4096


class Client:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.recv_buffer = RECV_BUFFER

    def register(self):
        pass

    def login(self):
        pass

    def chatall(self):
        pass

    @staticmethod
    def print_prompt():
        sys.stdout.write('[Me] ')
        sys.stdout.flush()

    def start_chat_client(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            sock.connect((self.host, self.PORT))
        except:
            print "Unable to connect"
            sys.exit()

        print("Connected")
        Client.print_prompt()

        while True:
            socket_list = [sys.stdin, sock]
            ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

            for ready_sock in ready_to_read:
                if ready_sock == sock:
                    # from remote msg
                    data = sock.recv(self.recv_buffer)
                    if data:
                        sys.stdout.write(data)
                        Client.print_prompt()
                    else:
                        print()
                        print("Disconected from server")
                else:
                    # from stdin
                    msg = sys.stdin.readline()
                    sock.send(msg)
                    Client.print_prompt()