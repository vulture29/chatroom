import sys
import socket
import select
import json
import struct

HOST = "127.0.0.1"
PORT = 9009
MAX_MSG_SIZE = 1024


class Client:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.logged_in = False
        self.user = "Guest"
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

    @staticmethod
    def write_stdout(message):
        sys.stdout.write(message)
        sys.stdout.flush()

    def register(self, para):
        # get username and password
        username = raw_input("Username: ")
        passwd = raw_input("Password: ")
        # TODO: check format
        register_info = {'type': 'register', 'username': username, 'passwd': passwd}
        self.send_socket(json.dumps(register_info))
        # self.print_prompt()
        return True

    def login(self, para):
        # get username and password
        username = raw_input("Username: ")
        passwd = raw_input("Password: ")
        login_info = {'type': 'login', 'username': username, 'passwd': passwd}
        self.send_socket(json.dumps(login_info))
        return True

    def create(self, para):
        # create chatroom
        create_info = {'type': 'create', 'room': para}
        self.send_socket(json.dumps(create_info))
        return True

    def enter(self, para):
        # enter chatroom
        enter_info = {'type': 'enter', 'room': para}
        self.send_socket(json.dumps(enter_info))
        return True

    def leave(self, para):
        # leave chatroom
        leave_info = {'type': 'leave'}
        self.send_socket(json.dumps(leave_info))
        return True

    def chat(self, para):
        # chat in current chatroom
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        if len(para) > MAX_MSG_SIZE:
            Client.write_stdout("Your message is too long. Max message size is " + MAX_MSG_SIZE)
            return True
        data = {'type': 'chat', 'message': para, 'user': self.user}
        self.send_socket(json.dumps(data))
        self.print_prompt()
        return True

    def chatat(self, para):
        # private chat with a user
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        if len(para) > MAX_MSG_SIZE:
            Client.write_stdout("Your message is too long. Max message size is " + MAX_MSG_SIZE)
            return True
        space_index = para.lstrip().find(' ')
        if space_index == -1:
            Client.write_stdout("You need to specify target user.\n")
            return True
        else:
            target = para[0:space_index]
            send_msg = para[space_index + 1:]
        data = {'type': 'chatat', 'message': send_msg, 'user': self.user, 'target': target}
        self.send_socket(json.dumps(data))
        self.print_prompt()
        return True

    def chatall(self, para):
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        if len(para) < 1:
            Client.write_stdout("Do not send empty message.\n")
            return True
        elif len(para) > MAX_MSG_SIZE:
            Client.write_stdout("Your message is too long. Max message size is " + MAX_MSG_SIZE)
            return True
        data = {'type': 'chatall', 'message': para, 'user': self.user}
        self.send_socket(json.dumps(data))
        self.print_prompt()
        return True

    def query(self, para):
        data = {'type': 'query', 'message': para, 'user': self.user}
        self.send_socket(json.dumps(data))
        self.print_prompt()
        return True

    def print_prompt(self):
        sys.stdout.write('[' + self.user + '] ')
        sys.stdout.flush()

    def invalid_command_prompt(self):
        # self.print_prompt()
        print("Invalid command. Please enter again.")
        self.print_prompt()

    def send_socket(self, msg):
        header = {'timestamp': 1, 'msg_length': len(msg)}
        head_str = bytes(json.dumps(header))
        head_len_str = struct.pack('i', len(head_str))
        self.sock.send(head_len_str)
        self.sock.send(head_str)
        self.sock.send(msg)

    def listen_socket(self):
        socket_list = [sys.stdin, self.sock]
        try:
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
                    input_str = sys.stdin.readline().lstrip()
                    space_index = input_str.find(' ')
                    command = input_str.strip() if space_index == -1 else input_str[0:space_index]
                    try:
                        command_func = getattr(self, command)
                    except AttributeError:
                        self.invalid_command_prompt()
                        continue
                    command_func(input_str[space_index + 1:] if space_index != -1 else '')
        except:
            print()
            print("Disconnected from server")
            sys.exit()

        return ret_data

    def start_chat_client(self):
        self.print_prompt()
        while True:
            data_list = self.listen_socket()
            for data in data_list:
                try:
                    self.print_prompt()
                    msg_dict = json.loads(data)
                    data_dict = msg_dict['data']
                    if data_dict['type'] in ('chat', 'chatall'):
                        Client.write_stdout('\n[' + msg_dict['source'] + '] ' + data_dict['message'])
                    elif data_dict['type'] == 'register':
                        if data_dict['status'] == 'success':
                            Client.write_stdout('Successfully registered!\n')
                        elif data_dict['status'] == 'exist':
                            Client.write_stdout('Your username has already been registered.\n' +
                                                'Try agin with another username.\n')
                        else:
                            Client.write_stdout('Fail to register.\n')
                    elif data_dict['type'] == 'login':
                        if data_dict['status'] == 'success':
                            self.user = data_dict['username']
                            self.logged_in = True
                            Client.write_stdout('You have logged in as ' + self.user + '\n')
                        elif data_dict['status'] == 'already':
                            Client.write_stdout('The username has already logged in.\n')
                        elif data_dict['status'] == 'fail':
                            Client.write_stdout('Your username or password is invalid. Try again.\n')
                    elif data_dict['type'] == 'query':
                        online_time = data_dict['online_time']
                        Client.write_stdout('Your total online time is ' + str(online_time) + 's\n')
                    self.print_prompt()
                except ValueError:
                    # non-structured msg
                    print("non-structured msg")
                    print(data)
                    self.print_prompt()

        self.sock.close()
        sys.exit()

