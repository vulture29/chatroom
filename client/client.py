import sys
import socket
import select
import json
import struct

HOST = "127.0.0.1"
PORT = 9009


class Client:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.logged_in = False
        self.user = "empty"
        self.sock = None
        self.init_client_socket(self.host, self.port)

    def init_client_socket(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2)  # random timeout
        try:
            self.sock.connect((host, port))
        except socket.error as msg:
            print("Unable to connect" + msg)
            sys.exit()
        except socket.timeout as msg:
            print("Connection timeout" + msg)
            sys.exit()
        print("Connected!")

    def check_user(self, username, passwd):
        return True

    def register(self, para):
        # get username and passwd
        username = "user1"
        passwd = "passwd1"

        return True

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
        self.send_socket(para)
        return True

    def quit(self, para):
        print("Exiting...")
        return False

    def print_prompt(self):
        sys.stdout.write('[' + self.user + '] ')
        sys.stdout.flush()

    def invalid_prompt(self):
        self.print_prompt()
        print("Invalid command. Please enter again.")

    def send_socket(self, msg):
        header = {'timestamp': 1, 'msg_length': len(msg), 'type': 'normal_msg'}
        head_str = bytes(json.dumps(header))
        head_len_str = struct.pack('i', len(head_str))
        self.sock.send(head_len_str)
        self.sock.send(head_str)
        self.sock.send(msg)

    def listen_socket(self):
        self.print_prompt()
        socket_list = [sys.stdin, self.sock]
        ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

        ret_data = []
        for ready_sock in ready_to_read:
            if ready_sock == self.sock:
                # from remote msg
                head_len_str = self.sock.recv(4)
                header_len = struct.unpack('i', head_len_str)[0]
                head_str = self.sock.recv(header_len)
                header = json.loads(head_str)
                real_data_len = header['msg_length']
                data = self.sock.recv(real_data_len)
                if data:
                    ret_data.append(data)
                else:
                    print()
                    print("Disconnected from server")
                    sys.exit()
            else:
                # from stdin
                input_str = sys.stdin.readline()
                space_index = input_str.find(' ')
                if space_index == -1:
                    self.invalid_prompt()
                    continue
                command = input_str[0:space_index]
                try:
                    command_func = getattr(self, command)
                except AttributeError:
                    self.invalid_prompt()
                    continue
                command_func(input_str[space_index + 1:])

        return ret_data

    def start_chat_client(self):
        while True:
            data_list = self.listen_socket()
            for data in data_list:
                sys.stdout.write(data)
                sys.stdout.flush()
        self.sock.close()
        sys.exit()
