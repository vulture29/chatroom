import sys
import socket
import select
from client_socket_operation import *

HOST = "127.0.0.1"
PORT = 9009


class Client:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.logged_in = False
        self.user = "empty"

    def check_user(self, username, passwd):
        return True

    def register(self, para):
        # get username and passwd
        username = "user1"
        passwd = "passwd1"

    def login(self, para):
        # get username and passwd
        username = "user1"
        passwd = "passwd1"
        if self.check_user(username, passwd):
            self.logged_in = True
            self.user = username
        else:
            print("Incorrect username or password.")
        return True

    def chatall(self, para):
        print("chatall")
        return True

    def quit(self, para):
        print("Exiting...")
        return False

    def print_prompt(self):
        sys.stdout.write('[' + self.user + ' ')
        sys.stdout.flush()

    def invalid_prompt(self):
        self.print_prompt()
        print("Invalid command. Please enter again.")

    def start_chat_client(self):
        while True:
            if self.logged_in:
                sock = init_client_socket(self.host, self.port)
                data_list = listen_socket(sock)
                for data in data_list:
                    sys.stdout.write(data)
                    self.print_prompt()
            else:
                input_str = raw_input()
                space_index = input_str.find(' ')
                if space_index == -1:
                    self.invalid_prompt()
                command = input_str[0:space_index]
                command_func = getattr(self, command)
                if not command_func(input_str[space_index+1:]):
                    break
        sys.exit()




    def start_chat_connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            sock.connect((self.host, self.PORT))
        except socket.error as msg:
            print("Unable to connect" + msg)
            sys.exit()
        except socket.timeout as msg:
            print("Connection timeout" + msg)
            sys.exit()

        print("Connected!")
        self.print_prompt()

        while True:
            socket_list = [sys.stdin, sock]
            ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

            for ready_sock in ready_to_read:
                if ready_sock == sock:
                    # from remote msg
                    data = sock.recv(self.recv_buffer)
                    if data:
                        sys.stdout.write(data)
                        self.print_prompt()
                    else:
                        print()
                        print("Disconnected from server")
                else:
                    # from stdin
                    msg = sys.stdin.readline()
                    sock.send(msg)
                    self.print_prompt()