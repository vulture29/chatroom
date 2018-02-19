import socket
import json
import struct

HOST = ''
SOCKET_LIST = []
RECV_BUFFER = 4096
PORT = 9009
MAX_LISTEN_NUM = 100


# broadcast chat messages to all connected clients
def broadcast(server_socket, from_sock, message):
    for sock in SOCKET_LIST:
        # send the message only to peer
        if sock != server_socket and sock != from_sock:
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


def init_server_socket():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # read it
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_LISTEN_NUM)

    return server_socket


def handle_new_connection(server_socket):
    sock, sock_addr = server_socket.accept()
    SOCKET_LIST.append(sock)
    print("Client (%s, %s) connected" % sock_addr)
    broadcast(server_socket, sock, "[%s:%s] entered chatting room\n" % sock_addr)


def handle_client_msg(server_socket, sock):
    try:
        head_len_str = sock.recv(4)
        header_len = struct.unpack('i', head_len_str)[0]
        head_str = sock.recv(header_len)
        header = json.loads(head_str)
        real_data_len = header['msg_length']
        data = sock.recv(real_data_len)
        # data = sock.recv(RECV_BUFFER)
        if data:
            broadcast(server_socket, sock, "\r" + '[' + str(sock.getpeername()) + '] ' + data)
        else:
            # remove broken socket
            if sock in SOCKET_LIST:
                SOCKET_LIST.remove(sock)
            print("Client " + str(sock.getpeername()) + " disconnected")
            broadcast(server_socket, sock, "Client " + str(sock.getpeername()) + " disconnected\n")
    except:
        if sock in SOCKET_LIST:
            SOCKET_LIST.remove(sock)
        print("Client " + str(sock.getpeername()) + " disconnected")
        broadcast(server_socket, sock, "Client " + str(sock.getpeername()) + " disconnected\n")