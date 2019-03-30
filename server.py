import select
import socket
import datetime

import networking

BROADCAST_INTERVAL_SECS = 5


def calc_next_broadcast_time():
    return datetime.datetime.now() + datetime.timedelta(0, BROADCAST_INTERVAL_SECS)


def build_time_message():
    """A dummy message to test that broadcast (publishing messages without an incoming message) works"""
    return {
        "m": "time",
        "time": datetime.datetime.now().replace(tzinfo=datetime.timezone.utc),
    }


class Server(object):
    def __init__(self):
        self.known_clients = {}
        self.next_broadcast_at = calc_next_broadcast_time()

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
                print("{} sockets need writes".format(len(sockets_needing_writes)))
            ready_to_read, ready_to_write, in_error = select.select(
                [server_socket] + list(self.known_clients.keys()),
                sockets_needing_writes,
                self.known_clients,
                timeout,
            )

            for sock in in_error:
                self.handle_errored_socket(sock)

            for sock in ready_to_write:
                self.handle_writable_socket(sock)

            for sock in ready_to_read:
                if sock == server_socket:
                    (client_socket, address) = server_socket.accept()
                    print("Accepting connection from {}".format(address))
                    self.known_clients[client_socket] = networking.Messenger(
                        client_socket
                    )
                    self.handle_readable_socket(client_socket)
                else:
                    self.handle_readable_socket(sock)

            if datetime.datetime.now() > self.next_broadcast_at:
                print(
                    "Sending server time broadcast to all {} connected clients".format(
                        len(self.known_clients)
                    )
                )
                self.next_broadcast_at = calc_next_broadcast_time()
                for client in self.known_clients.values():
                    client.queue_message(
                        networking.BROADCAST_TRANSACTION_ID, build_time_message()
                    )

    def handle_errored_socket(self, sock):
        print("socket in error", socket.getpeername())
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
