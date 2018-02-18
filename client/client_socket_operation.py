import socket
import sys
import select

RECV_BUFFER = 4096


def init_client_socket(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)

    try:
        sock.connect((host, port))
    except socket.error as msg:
        print("Unable to connect" + msg)
        sys.exit()
    except socket.timeout as msg:
        print("Connection timeout" + msg)
        sys.exit()
    print("Connected!")
    return sock


def listen_socket(sock):
    socket_list = [sys.stdin, sock]
    ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

    ret_data = []
    for ready_sock in ready_to_read:
        if ready_sock == sock:
            # from remote msg
            data = sock.recv(RECV_BUFFER)
            if data:
                ret_data.append(data)
            else:
                print()
                print("Disconnected from server")
                sys.exit()

        else:
            # from stdin
            msg = sys.stdin.readline()
            send_socket(sock, msg)

    return ret_data


def send_socket(sock, msg):
    sock.send(msg)