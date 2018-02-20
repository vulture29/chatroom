import select
import socket
import json
import struct
import shelve
import time
import threading

HOST = ''
PORT = 9009
MAX_LISTEN_NUM = 100
USER_RECORD_FILE_PATH = '/Users/xingyao/Documents/Vulture/study/netease/chatroom/user_record'
USER_ONLINE_RECORD_FILE_PATH = '/Users/xingyao/Documents/Vulture/study/netease/chatroom/user_online_record'


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
        self.user_online_dict = None
        self.user_dict = None
        self.server_socket = None
        self.init_db()
        self.init_server_socket()

    def init_db(self):
        self.user_online_dict = shelve.open(USER_ONLINE_RECORD_FILE_PATH)
        # set all login lock to False
        for user in self.user_online_dict.keys():
            tmp_user_dict = self.user_online_dict.get(user)
            tmp_user_dict['login_lock'] = False
        self.user_dict = shelve.open(USER_RECORD_FILE_PATH)

    def init_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # read it
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_LISTEN_NUM)

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
        user_dict = self.user_online_dict.get(user)
        user_login_list = user_dict.get('login_time', [])
        user_logout_list = user_dict.get('logout_time', [])
        if user_dict.get('login_lock'):
            total_online_time += time.time()
        for offline_time in user_logout_list:
            total_online_time += offline_time
        for online_time in user_login_list:
            total_online_time -= online_time
        return total_online_time

    # broadcast chat messages to all connected clients
    def broadcast(self, from_sock, message):
        for connection in self.connection_list:
            sock = connection.sock
            # send the message only to peer
            if sock != self.server_socket and sock != from_sock:
                self.send_socket(sock, message)

    def handle_new_connection(self):
        sock, sock_addr = self.server_socket.accept()
        connection = Connection(sock)
        self.connection_list.append(connection)
        print("Client (%s, %s) connected" % sock_addr)
        # self.broadcast(sock, "%s entered chatting room\n" % connection.user)

    def handle_register(self, sock, user_info):
        username = str(user_info['username'])
        passwd = str(user_info['passwd'])
        if username not in self.user_dict:
            self.user_dict[username] = passwd
            register_info = {'type': 'register', 'status': "success"}
            message = {'source': str(sock.getpeername()), 'data': register_info}
            self.send_socket(sock, json.dumps(message))
        else:
            register_info = {'type': 'register', 'status': "exist"}
            message = {'source': str(sock.getpeername()), 'data': register_info}
            self.send_socket(sock, json.dumps(message))

    def handle_login(self, sock, user_info):
        username = str(user_info['username'])
        passwd = str(user_info['passwd'])
        if username not in self.user_online_dict:
            self.user_online_dict[username] = {'login_lock': False, 'login_time': [], 'logout_time': []}
        if self.user_online_dict.get(username).get('login_lock', False):
            status = 'already'
        elif self.user_dict.get(username) == passwd:
            status = 'success'
        else:
            status = 'fail'
        login_info = {'type': 'login', 'status': status, 'username': username}
        message = {'source': str(sock.getpeername()), 'data': login_info}
        self.send_socket(sock, json.dumps(message))

        # successfully login
        if status == 'success':
            for connection in self.connection_list:
                if connection.sock == sock:
                    connection.user = username
            tmp_user_dict = self.user_online_dict[username]
            tmp_user_dict['login_lock'] = True
            tmp_user_dict['login_time'].append(time.time())
            self.user_online_dict[username] = tmp_user_dict
            self.broadcast(sock, "%s entered chatting room\n" % username)

    def handle_disconnect(self, sock, data=None):
        for connection in self.connection_list:
            if connection.sock == sock:
                username = connection.user
                tmp_user_dict = self.user_online_dict[username]
                tmp_user_dict['login_lock'] = False
                tmp_user_dict['logout_time'].append(time.time())
                self.user_online_dict[username] = tmp_user_dict
                self.remove_sock(sock)
                print("Client " + str(sock.getpeername()) + " disconnected")
                self.broadcast(sock, "Client " + str(sock.getpeername()) + " disconnected\n")

    def handle_chat(self, sock, data):
        message = {'source': data['user'], 'data': data}
        self.broadcast(sock, "\r" + json.dumps(message))

    def handle_query(self, sock, data):
        username = self.get_username(sock)
        online_time = self.get_online_time(username)
        query_info = {'type': 'query', 'online_time': online_time, 'username': username}
        message = {'source': str(sock.getpeername()), 'data': query_info}
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
                print('[' + str(sock.getpeername()) + '] ' + data)
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

        except Exception as e:
            print(e)
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
                    # t_handle_new_connection = threading.Thread(target=self.handle_new_connection, name='new_connection')
                    # t_handle_new_connection.start()
                    self.handle_new_connection()
                # msg from an existing connection
                else:
                    # t_handle_client_msg = threading.Thread(target=self.handle_client_msg,
                    #                                        args=(sock,), name='_client_msg')
                    # t_handle_client_msg.start()
                    self.handle_client_msg(sock)
        server_socket.close()