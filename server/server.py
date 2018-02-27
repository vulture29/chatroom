# -*- coding: utf-8 -*-

import select
import socket
import json
import struct
import time

HOST = ''
PORT = 9009
MAX_LISTEN_NUM = 100
USER_RECORD_FILE_PATH = '/Users/xingyao/Documents/Vulture/study/netease/chatroom/server/user_record'
USER_ONLINE_RECORD_FILE_PATH = '/Users/xingyao/Documents/Vulture/study/netease/chatroom/server/user_online_record'
CHAT_ROOM_RECORD_FILE_PATH = '/Users/xingyao/Documents/Vulture/study/netease/chatroom/server/chatroom_record'


class Connection:
    def __init__(self, sock, user="Guest"):
        self.sock = sock
        self.user = user
        self.logged_in = True


class Server:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.connection_list = []
        self.init_db()
        self.init_server_socket()

    def init_db(self):
        user_online_dict = Server.load_dict(USER_ONLINE_RECORD_FILE_PATH)
        chatroom_dict = Server.load_dict(CHAT_ROOM_RECORD_FILE_PATH)
        # set all login lock to False
        for user in user_online_dict.keys():
            tmp_user_dict = user_online_dict.get(user)
            tmp_user_dict['login_lock'] = False
            user_online_dict[user] = tmp_user_dict
        Server.write_dict(USER_ONLINE_RECORD_FILE_PATH, user_online_dict)
        # set chatroom record to empty
        Server.write_dict(CHAT_ROOM_RECORD_FILE_PATH, {})

    @staticmethod
    def load_dict(file_path):
        try:
            with open(file_path) as f:
                load_dict = json.load(f)
            return load_dict
        except Exception as e:
            print(file_path + ' load fail: ' + str(e))
            return {}

    @staticmethod
    def write_dict(file_path, data_dict):
        try:
            with open(file_path, 'w') as f:
                json.dump(data_dict, f)
        except Exception as e:
            print(file_path + ' write fail: ' + str(e))
            return {}

    def init_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # read it
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_LISTEN_NUM)

    def get_user_from_sock(self, sock):
        for connection in self.connection_list:
            if connection.sock == sock:
                return connection.user
        return None

    def send_socket(self, sock, message):
        try:
            header = {'timestamp': 1, 'msg_length': len(message)}
            head_str = bytes(json.dumps(header))
            head_len_str = struct.pack('i', len(head_str))
            sock.send(head_len_str)
            sock.send(head_str)
            sock.send(message)
        except:
            # broken socket connection
            sock.close()
            # broken socket, remove it
            self.handle_disconnect(sock)

    def remove_sock(self, sock):
        for connection in self.connection_list:
            if connection.sock == sock:
                self.connection_list.remove(connection)

    def get_username(self, sock):
        for connection in self.connection_list:
            if connection.sock == sock:
                return connection.user
        return None

    def get_online_time(self, user):
        total_online_time = 0
        user_online_dict = Server.load_dict(USER_ONLINE_RECORD_FILE_PATH)
        user_dict = user_online_dict.get(user)
        user_login_list = user_dict.get('login_time', [])
        user_logout_list = user_dict.get('logout_time', [])
        if user_dict.get('login_lock'):
            total_online_time += time.time()
        for offline_time in user_logout_list:
            total_online_time += offline_time
        for online_time in user_login_list:
            total_online_time -= online_time
        return int(total_online_time)

    def send_to_target(self, from_sock, target, message):
        target_found = False
        for connection in self.connection_list:
            if connection.user == target:
                target_found = True
                self.send_socket(connection.sock, message)
        if not target_found:
            room_info = {'type': 'chatat', 'status': "no user"}
            fail_message = {'source': str(self.get_user_from_sock(from_sock)), 'data': room_info}
            self.send_socket(from_sock, json.dumps(fail_message))

    def broadcast_room(self, from_sock, room, message):
        connection_list = []
        chatroom_dict = Server.load_dict(CHAT_ROOM_RECORD_FILE_PATH)
        if chatroom_dict.get(str(room)) is None:
            room_info = {'type': 'chat', 'status': "no room"}
            fail_message = {'source': str(self.get_user_from_sock(from_sock)), 'data': room_info}
            self.send_socket(from_sock, json.dumps(fail_message))
            return
        if self.get_user_from_sock(from_sock) not in chatroom_dict.get(str(room)):
            room_info = {'type': 'chat', 'status': "not in room"}
            fail_message = {'source': str(self.get_user_from_sock(from_sock)), 'data': room_info}
            self.send_socket(from_sock, json.dumps(fail_message))
            return
        for username in chatroom_dict.get(str(room)):
            connection_list.append(
                [connection for connection in self.connection_list if connection.user == username][0])
        self.broadcast(from_sock, message, connection_list)

    # broadcast chat messages to all connected clients
    def broadcast(self, from_sock, message, connection_list=None):
        if connection_list is None or len(connection_list) == 0:
            connection_list = self.connection_list
        for connection in connection_list:
            sock = connection.sock
            # send the message only to peer
            if sock != self.server_socket and sock != from_sock and self.get_user_from_sock(sock) != 'Guest':
                self.send_socket(sock, message)

    def handle_new_connection(self):
        sock, sock_addr = self.server_socket.accept()
        connection = Connection(sock)
        self.connection_list.append(connection)
        print("Client (%s, %s) connected" % sock_addr)
        # self.broadcast(sock, "%s entered chatting room\n" % connection.user)

    def handle_disconnect(self, sock, data=None):
        username = self.get_user_from_sock(sock)
        chatroom_dict = Server.load_dict(CHAT_ROOM_RECORD_FILE_PATH)
        for chatroom in chatroom_dict.keys():
            if username in chatroom_dict.get(chatroom):
                member_list = chatroom_dict.get(chatroom)
                member_list.remove(username)
                chatroom_dict[chatroom] = member_list
        Server.write_dict(CHAT_ROOM_RECORD_FILE_PATH, chatroom_dict)

        for connection in self.connection_list:
            if connection.sock == sock:
                username = connection.user
                user_online_dict = Server.load_dict(USER_ONLINE_RECORD_FILE_PATH)
                if user_online_dict.get(username) is None:
                    self.remove_sock(sock)
                    return
                tmp_user_dict = user_online_dict[username]
                tmp_user_dict['login_lock'] = False
                tmp_user_dict['logout_time'].append(time.time())
                user_online_dict[username] = tmp_user_dict
                Server.write_dict(USER_ONLINE_RECORD_FILE_PATH, user_online_dict)
                self.remove_sock(sock)
                print("Client " + username + " disconnected")

    def handle_register(self, sock, user_info):
        username = str(user_info['username'])
        passwd = str(user_info['passwd'])
        user_dict = Server.load_dict(USER_RECORD_FILE_PATH)
        if username not in user_dict:
            user_dict[username] = passwd
            Server.write_dict(USER_RECORD_FILE_PATH, user_dict)
            register_info = {'type': 'register', 'status': "success"}
            message = {'source': str(self.get_user_from_sock(sock)), 'data': register_info}
            self.send_socket(sock, json.dumps(message))
        else:
            register_info = {'type': 'register', 'status': "exist"}
            message = {'source': str(self.get_user_from_sock(sock)), 'data': register_info}
            self.send_socket(sock, json.dumps(message))

    def handle_login(self, sock, user_info):
        username = str(user_info['username'])
        passwd = str(user_info['passwd'])
        user_online_dict = Server.load_dict(USER_ONLINE_RECORD_FILE_PATH)
        if username not in user_online_dict:
            user_online_dict[username] = {'login_lock': False, 'login_time': [], 'logout_time': []}
            Server.write_dict(USER_ONLINE_RECORD_FILE_PATH, user_online_dict)
        user_online_dict = Server.load_dict(USER_ONLINE_RECORD_FILE_PATH)
        user_dict = Server.load_dict(USER_RECORD_FILE_PATH)
        if user_dict.get(username) != passwd:
            status = 'fail'
        elif user_online_dict.get(username).get('login_lock', False):
            status = 'already'
        else:
            status = 'success'
        login_info = {'type': 'login', 'status': status, 'username': username}
        message = {'source': str(self.get_user_from_sock(sock)), 'data': login_info}
        self.send_socket(sock, json.dumps(message))

        # successfully login
        if status == 'success':
            for connection in self.connection_list:
                if connection.sock == sock:
                    connection.user = username
            tmp_user_dict = user_online_dict[username]
            tmp_user_dict['login_lock'] = True
            tmp_user_dict['login_time'].append(time.time())
            user_online_dict[username] = tmp_user_dict
            Server.write_dict(USER_ONLINE_RECORD_FILE_PATH, user_online_dict)
            self.broadcast(sock, "%s entered chatting room\n" % username)

    def handle_create(self, sock, data):
        room_name = str(data['room'])
        username = str(data['user'])
        chatroom_dict = Server.load_dict(CHAT_ROOM_RECORD_FILE_PATH)
        if room_name in chatroom_dict:
            status = 'already'
        else:
            chatroom_dict[room_name] = []
            Server.write_dict(CHAT_ROOM_RECORD_FILE_PATH, chatroom_dict)
            status = 'success'
        create_info = {'type': 'create', 'status': status}
        message = {'source': username, 'data': create_info}
        self.send_socket(sock, json.dumps(message))

    def handle_enter(self, sock, data):
        room_name = str(data['room'])
        username = str(data['user'])
        chatroom_dict = Server.load_dict(CHAT_ROOM_RECORD_FILE_PATH)
        if room_name not in chatroom_dict:
            status = 'not exist'
        else:
            member_list = chatroom_dict.get(room_name)
            if username in member_list:
                status = 'already'
            else:
                member_list.append(username)
                chatroom_dict[room_name] = member_list
                Server.write_dict(CHAT_ROOM_RECORD_FILE_PATH, chatroom_dict)
                status = 'success'
        enter_info = {'type': 'enter', 'status': status}
        message = {'source': username, 'data': enter_info}
        self.send_socket(sock, json.dumps(message))

    def handle_leave(self, sock, data):
        username = str(data['user'])
        room_name = str(data['room'])
        found_flag = False
        chatroom_dict = Server.load_dict(CHAT_ROOM_RECORD_FILE_PATH)
        for chatroom in chatroom_dict.keys():
            if username in chatroom_dict.get(chatroom):
                found_flag = True
                break
        if not found_flag:
            status = 'not inside'
        else:
            if len(room_name) > 0:
                member_list = chatroom_dict.get(room_name)
                if username in member_list:
                    member_list.remove(username)
                    chatroom_dict[room_name] = member_list
                    Server.write_dict(CHAT_ROOM_RECORD_FILE_PATH, chatroom_dict)
                    status = 'success1'
                else:
                    status = 'not inside'
            else:
                for chatroom in chatroom_dict.keys():
                    if username in chatroom_dict.get(chatroom):
                        member_list = chatroom_dict.get(chatroom)
                        member_list.remove(username)
                        chatroom_dict[room_name] = member_list
                        status = 'success2'
                Server.write_dict(CHAT_ROOM_RECORD_FILE_PATH, chatroom_dict)
        leave_info = {'type': 'leave', 'status': status}
        message = {'source': username, 'data': leave_info}
        self.send_socket(sock, json.dumps(message))

    def handle_chat(self, sock, data):
        room = data['room']
        message = {'place': 'Room: ' + room, 'source': data['user'], 'data': data}
        self.broadcast_room(sock, room,  "\r" + json.dumps(message))

    def handle_chatat(self, sock, data):
        message = {'place': 'Private', 'source': data['user'], 'data': data}
        target = str(data['target'])
        self.send_to_target(sock, target, "\r" + json.dumps(message))

    def handle_chatall(self, sock, data):
        message = {'place': 'Lobby', 'source': data['user'], 'data': data}
        self.broadcast(sock, "\r" + json.dumps(message))

    def handle_query(self, sock, data):
        username = self.get_username(sock)
        online_time = self.get_online_time(username)
        query_info = {'type': 'query', 'online_time': online_time, 'username': username}
        message = {'source': str(self.get_user_from_sock(sock)), 'data': query_info}
        self.send_socket(sock, json.dumps(message))

    def handle_client_msg(self, sock):
        try:
            head_len_str = sock.recv(4)
            header_len = struct.unpack('i', head_len_str)[0]
            head_str = sock.recv(header_len)
            header = json.loads(head_str)
            real_data_len = header['msg_length']
            recv_size = 0
            while recv_size < real_data_len:
                data = sock.recv(real_data_len-recv_size)
                recv_size += len(data)
            if data:
                print('[' + str(self.get_user_from_sock(sock)) + '] ' + data)
                data_dict = json.loads(data)
                msg_type = data_dict['type']
                try:
                    command_func = getattr(self, 'handle_' + msg_type)
                except AttributeError:
                    print("message type not valid")
                    return
                command_func(sock, data_dict)
            else:
                # remove broken socket
                self.handle_disconnect(sock)

        except:
            self.handle_disconnect(sock)

    def start_chat_server(self):
        self.connection_list.append(Connection(self.server_socket))
        print("Chat server started on port" + str(PORT))

        while True:
            ready_to_read, ready_to_write, in_error = select.select(
                [connection.sock for connection in self.connection_list], [], [], 0)

            for sock in ready_to_read:
                # new connection request
                if sock == self.server_socket:
                    self.handle_new_connection()
                # msg from an existing connection
                else:
                    self.handle_client_msg(sock)
        server_socket.close()
