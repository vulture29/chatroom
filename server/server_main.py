import select
from socket_operation import *


def start_chat_server():
    server_socket = init_server_socket()

    SOCKET_LIST.append(server_socket)

    print("Chat server started on port" + str(PORT))

    while True:
        ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST, [], [], 0)

        for sock in ready_to_read:
            # new connection request
            if sock == server_socket:
                handle_new_connection(sock)
            # msg from an existing connection
            else:
                handle_client_msg(server_socket, sock)

    server_socket.close()


if __name__ == "__main__":
    start_chat_server()