# -*- coding: utf-8 -*-

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

    @staticmethod
    def valid_account(username, passwd):
        if username == "Guest":
            return False
        if len(username) < 1 or len(passwd) < 1:
            return False
        # can add more constraints
        return True

    def register(self, para):
        # get username and password
        username = raw_input("Username: ")
        passwd = raw_input("Password: ")
        if not Client.valid_account(username, passwd):
            return True
        register_info = {'type': 'register', 'username': username, 'passwd': passwd}
        self.send_socket(json.dumps(register_info))
        return True

    def login(self, para):
        if self.logged_in:
            Client.write_stdout("You have already logged in as " + self.user)
            return True
        # get username and password
        username = raw_input("Username: ")
        passwd = raw_input("Password: ")
        login_info = {'type': 'login', 'username': username, 'passwd': passwd}
        self.send_socket(json.dumps(login_info))
        return True

    def create(self, para):
        # create chatroom
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        create_info = {'type': 'create', 'user': self.user, 'room': para.strip()}
        self.send_socket(json.dumps(create_info))
        return True

    def enter(self, para):
        # enter chatroom
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        enter_info = {'type': 'enter', 'user': self.user, 'room': para.strip()}
        self.send_socket(json.dumps(enter_info))
        return True

    def leave(self, para):
        # leave chatroom
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        leave_info = {'type': 'leave', 'user': self.user, 'room': para}
        self.send_socket(json.dumps(leave_info))
        return True

    def chat(self, para):
        # chat in current chatroom
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        space_index = para.lstrip().find(' ')
        if space_index == -1:
            Client.write_stdout("Usage: chat (room name) (message)\n")
            return True
        room = para[0:space_index]
        send_msg = para[space_index + 1:]
        if len(send_msg) > MAX_MSG_SIZE:
            Client.write_stdout("Your message is too long. Max message size is " + MAX_MSG_SIZE)
            return True
        data = {'type': 'chat', 'message': send_msg, 'user': self.user,  'room': room}
        self.send_socket(json.dumps(data))
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
        return True

    def query(self, para):
        if not self.logged_in:
            Client.write_stdout("You need to log in before chatting\n")
            return True
        data = {'type': 'query', 'message': para, 'user': self.user}
        self.send_socket(json.dumps(data))
        return True

    def exit(self):
        sys.exit()

    def print_prompt(self):
        sys.stdin.flush()
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
                    self.print_prompt()
        except:
            print()
            print("Disconnected from server")
            sys.exit()
        return ret_data

    def handle_register(self, data_dict, msg_dict):
        if str(data_dict['status']) == 'success':
            Client.write_stdout('Successfully registered!\n')
        elif str(data_dict['status']) == 'exist':
            Client.write_stdout('Your username has already been registered.\n' +
                                'Try agin with another username.\n')
        else:
            Client.write_stdout('Fail to register.\n')

    def handle_login(self, data_dict, msg_dict):
        if str(data_dict['status']) == 'success':
            self.user = str(data_dict['username'])
            self.logged_in = True
            Client.write_stdout('You have logged in as ' + self.user + '\n')
        elif str(data_dict['status']) == 'already':
            Client.write_stdout('The username has already logged in.\n')
        elif str(data_dict['status']) == 'fail':
            Client.write_stdout('Your username or password is invalid. Try again.\n')

    def handle_query(self, data_dict, msg_dict):
        online_time = data_dict['online_time']
        Client.write_stdout('Your total online time is ' + str(online_time) + 's\n')

    def handle_create(self, data_dict, msg_dict):
        if str(data_dict['status']) == 'already':
            Client.write_stdout('The chatroom is already existed.\n')
        elif str(data_dict['status']) == 'success':
            Client.write_stdout('Created chatroom successfully.\n')

    def handle_enter(self, data_dict, msg_dict):
        if str(data_dict['status']) == 'already':
            Client.write_stdout('You are already in this chatroom.\n')
        elif str(data_dict['status']) == 'not exist':
            Client.write_stdout('The chatroom is not existed.\n')
        elif str(data_dict['status']) == 'success':
            Client.write_stdout('Enter chatroom successfully.\n')

    def handle_leave(self, data_dict, msg_dict):
        if str(data_dict['status']) == 'not inside':
            Client.write_stdout('You are not inside this chatroom.\n')
        elif 'success' in str(data_dict['status']):
            Client.write_stdout('Left chatroom successfully.\n')

    def handle_chat(self, data_dict, msg_dict):
        if str(data_dict.get('status')) == 'no room' or str(data_dict.get('status')) == 'not in room':
            Client.write_stdout('You are not inside this chatroom.\n')
        else:
            Client.write_stdout('\n[' + str(msg_dict['place'] + '][' +
                                str(msg_dict['source'] + '] ' + str(data_dict['message']))))

    def handle_chatat(self, data_dict, msg_dict):
        if str(data_dict.get('status')) == 'no user':
            Client.write_stdout('Your target user is not online or not existed.\n')
        else:
            Client.write_stdout('\n[' + str(msg_dict['place']) + '][' +
                                str(msg_dict['source']) + '] ' + str(data_dict['message']))

    def handle_chatall(self, data_dict, msg_dict):
        Client.write_stdout('\n[' + str(msg_dict['place'] + '][' +
                            str(msg_dict['source']) + '] ' + str(data_dict['message'])))

    def start_chat_client(self):
        self.print_prompt()
        while True:
            data_list = self.listen_socket()
            for data in data_list:
                try:
                    msg_dict = json.loads(data)
                    data_dict = msg_dict['data']
                    handle_command = data_dict.get('type')
                    try:
                        handle_command_func = getattr(self, 'handle_' + handle_command)
                    except AttributeError:
                        continue
                    handle_command_func(data_dict, msg_dict)
                    self.print_prompt()
                except ValueError:
                    pass

        self.sock.close()
        sys.exit()

