import select
import socket
import json
import struct

HOST = ''
SOCKET_LIST = []
RECV_BUFFER = 4096
PORT = 9009
MAX_LISTEN_NUM = 100


class Server:
    def __init__(self):
        self.server_socket = None
        self.init_server_socket()

    def init_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # read it
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(MAX_LISTEN_NUM)

    # broadcast chat messages to all connected clients
    def broadcast(self, from_sock, message):
        for sock in SOCKET_LIST:
            # send the message only to peer
            if sock != self.server_socket and sock != from_sock:
                try:
                    header = {'timestamp': 1, 'msg_length': len(message), 'type': 'normal_msg'}
                    head_str = bytes(json.dumps(header))
                    head_len_str = struct.pack('i', len(head_str))
                    sock.send(head_len_str)
                    sock.send(head_str)
                    sock.send(message)
                except:
                    # broken socket connection
                    sock.close()
                    # broken socket, remove it
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)

    def handle_new_connection(self):
        sock, sock_addr = self.server_socket.accept()
        SOCKET_LIST.append(sock)
        print("Client (%s, %s) connected" % sock_addr)
        self.broadcast(sock, "[%s:%s] entered chatting room\n" % sock_addr)

    def handle_register(self, user_info):
        usename = user_info['username']
        passwd = user_info['passwd']

    def handle_login(self, user_info):
        usename = user_info['username']
        passwd = user_info['passwd']

    def handle_client_msg(self, sock):
        try:
            head_len_str = sock.recv(4)
            header_len = struct.unpack('i', head_len_str)[0]
            head_str = sock.recv(header_len)
            header = json.loads(head_str)
            real_data_len = header['msg_length']
            data = sock.recv(real_data_len)
            # data = sock.recv(RECV_BUFFER)
            if data:
                print('[' + str(sock.getpeername()) + '] ' + data)
                data_dict = json.loads(data)
                if data_dict['type'] == 'chat':
                    message = {'source': str(sock.getpeername()), 'data': data}
                    self.broadcast(sock, "\r" + json.dumps(message))
                elif data_dict['type'] == 'register':
                    self.handle_register(data_dict)
                elif data_dict['type'] == 'login':
                    self.handle_login(data_dict)
            else:
                # remove broken socket
                if sock in SOCKET_LIST:
                    SOCKET_LIST.remove(sock)
                print("Client " + str(sock.getpeername()) + " disconnected")
                self.broadcast(sock, "Client " + str(sock.getpeername()) + " disconnected\n")
        except:
            if sock in SOCKET_LIST:
                SOCKET_LIST.remove(sock)
            print("Client " + str(sock.getpeername()) + " disconnected")
            self.broadcast(sock, "Client " + str(sock.getpeername()) + " disconnected\n")

    def start_chat_server(self):
        SOCKET_LIST.append(self.server_socket)
        print("Chat server started on port" + str(PORT))

        while True:
            ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST, [], [], 0)

            for sock in ready_to_read:
                # new connection request
                if sock == self.server_socket:
                    self.handle_new_connection()
                # msg from an existing connection
                else:
                    self.handle_client_msg(sock)
        server_socket.close()