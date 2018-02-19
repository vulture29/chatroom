import select
import socket
import json
import struct
import shelve

HOST = ''
PORT = 9009
MAX_LISTEN_NUM = 100
USER_RECORD_FILE_PATH = '/Users/xingyao/Desktop/user_record'


class Server:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.socket_list = []
        self.server_socket = None
        self.init_server_socket()

    def init_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # read it
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(MAX_LISTEN_NUM)

    @staticmethod
    def send_socket(sock, message):
        header = {'timestamp': 1, 'msg_length': len(message)}
        head_str = bytes(json.dumps(header))
        head_len_str = struct.pack('i', len(head_str))
        sock.send(head_len_str)
        sock.send(head_str)
        sock.send(message)

    # broadcast chat messages to all connected clients
    def broadcast(self, from_sock, message):
        for sock in self.socket_list:
            # send the message only to peer
            if sock != self.server_socket and sock != from_sock:
                try:
                    Server.send_socket(sock, message)
                except:
                    # broken socket connection
                    sock.close()
                    # broken socket, remove it
                    if sock in self.socket_list:
                        self.socket_list.remove(sock)

    def handle_new_connection(self):
        sock, sock_addr = self.server_socket.accept()
        self.socket_list.append(sock)
        print("Client (%s, %s) connected" % sock_addr)
        self.broadcast(sock, "[%s:%s] entered chatting room\n" % sock_addr)

    def handle_register(self, sock, user_info):
        username = user_info['username']
        passwd = user_info['passwd']
        user_dict = shelve.open(USER_RECORD_FILE_PATH)
        if username not in user_dict:
            user_dict[username] = passwd
            register_info = {'type': 'register', 'status': "success"}
            message = {'source': str(sock.getpeername()), 'data': register_info}
            Server.send_socket(sock, json.dumps(message))
        else:
            register_info = {'type': 'register', 'status': "exist"}
            message = {'source': str(sock.getpeername()), 'data': register_info}
            Server.send_socket(sock, json.dumps(message))

        user_dict.close()

    def handle_login(self, sock, user_info):
        username = user_info['username']
        passwd = user_info['passwd']
        user_dict = shelve.open(USER_RECORD_FILE_PATH)
        if username not in user_dict or user_dict[username] != passwd:
            status = 'fail'
        else:
            status = 'success'
        login_info = {'type': 'login', 'status': status, 'username': username}
        message = {'source': str(sock.getpeername()), 'data': login_info}
        Server.send_socket(sock, json.dumps(message))

        user_dict.close()

    def handle_chat(self, sock, data):
        message = {'source': data['user'], 'data': data}
        self.broadcast(sock, "\r" + json.dumps(message))

    def handle_client_msg(self, sock):
        try:
            head_len_str = sock.recv(4)
            header_len = struct.unpack('i', head_len_str)[0]
            head_str = sock.recv(header_len)
            header = json.loads(head_str)
            real_data_len = header['msg_length']
            data = sock.recv(real_data_len)
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
                if sock in self.socket_list:
                    self.socket_list.remove(sock)
                print("Client " + str(sock.getpeername()) + " disconnected")
                self.broadcast(sock, "Client " + str(sock.getpeername()) + " disconnected\n")
        except:
            if sock in self.socket_list:
                self.socket_list.remove(sock)
            print("Client " + str(sock.getpeername()) + " disconnected")
            self.broadcast(sock, "Client " + str(sock.getpeername()) + " disconnected\n")

    def start_chat_server(self):
        self.socket_list.append(self.server_socket)
        print("Chat server started on port" + str(PORT))

        while True:
            ready_to_read, ready_to_write, in_error = select.select(self.socket_list, [], [], 0)

            for sock in ready_to_read:
                # new connection request
                if sock == self.server_socket:
                    self.handle_new_connection()
                # msg from an existing connection
                else:
                    self.handle_client_msg(sock)
        server_socket.close()