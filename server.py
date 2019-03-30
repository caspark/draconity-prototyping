import select
import socket

import networking


class Server(object):
    def __init__(self):
        self.known_clients = {}

    def serve(self):
        host_and_port = (socket.gethostname(), 8000)
        connection_backlog_limit = 5

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setblocking(False)
        server_socket.bind(host_and_port)
        server_socket.listen(connection_backlog_limit)
        print("server listening on", host_and_port)

        while True:
            timeout = 0.01  # in seconds
            sockets_needing_writes = [
                s for s, c in self.known_clients.items() if c.has_messages_to_send()
            ]
            if len(sockets_needing_writes) > 0:
                print("{} sockets needing writes".format(len(sockets_needing_writes)))
            ready_to_read, ready_to_write, in_error = select.select(
                [server_socket] + list(self.known_clients.keys()),
                sockets_needing_writes,
                self.known_clients,
                timeout,
            )
            if len(ready_to_read) > 0 or len(ready_to_write) > 0 or len(in_error) > 0:
                print(
                    "select results: rlist={}, wlist={}, xlist={}".format(
                        ready_to_read, ready_to_write, in_error
                    )
                )

            for sock in in_error:
                self.handle_errored_socket(sock)

            for sock in ready_to_write:
                self.handle_writable_socket(sock)

            for sock in ready_to_read:
                if sock == server_socket:
                    (client_socket, address) = server_socket.accept()
                    print("{} is new connection from {}".format(client_socket, address))
                    self.known_clients[client_socket] = networking.Messenger(
                        client_socket
                    )
                    self.handle_readable_socket(client_socket)
                else:
                    self.handle_readable_socket(sock)

    def handle_errored_socket(self, sock):
        print("socket in error", socket)
        if sock in self.known_clients:
            del self.known_clients[sock]

    def handle_writable_socket(self, sock):
        if sock not in self.known_clients:
            return

        try:
            self.known_clients[sock].send_messages()
        except networking.MessengerConnectionBroken as e:
            print("Handling broken connection send error by removing client:", e)
            del self.known_clients[sock]

    def handle_readable_socket(self, sock):
        if sock not in self.known_clients:
            return

        client = self.known_clients[sock]
        try:
            for tid, message in client.read_messages():
                self.handle_message(client, tid, message)
        except networking.MessengerBufferFullError as e:
            print("Handling full buffer read error by removing client:", e)
            sock.close()
            del self.known_clients[sock]
        except networking.MessengerConnectionBroken as e:
            print("Handling broken connection read error by removing client:", e)
            del self.known_clients[sock]

    def handle_message(self, client, tid, message):
        if "m" not in message:
            print("unrecognized message, tid: {}  message: {}".format(tid, message))
            return
        method = message["m"]

        if method == "ping":
            client.queue_message(tid, {"m": "pong", "c": message["c"]})
        else:
            print("unrecognized message method:", method)


if __name__ == "__main__":
    Server().serve()
