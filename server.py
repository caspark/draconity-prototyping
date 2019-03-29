import socket

import select
import struct
import bson

from ring_buffer import RingBuffer
import networking


class MessageParser(object):
    def __init__(self):
        # used for state-machine of reading from inbound data buffer
        self.tid = None
        self.len = None
        self.msg = None

    def try_parse(self, ring_buffer):
        header_size = struct.calcsize(networking.MSG_HEADER_FMT)
        if self.tid is None and ring_buffer.bytes_used() >= header_size:
            self.tid, self.len = struct.unpack(
                networking.MSG_HEADER_FMT, ring_buffer.read_exactly(header_size)
            )
        else:
            return
        if self.msg is None and ring_buffer.bytes_used() >= self.len:
            self.msg = bson.loads(ring_buffer.read_exactly(self.len))
        else:
            return

        r = (self.tid, self.msg)
        self.tid = None
        self.len = None
        self.msg = None
        return r


class Client(object):
    def __init__(self, socket):
        self.socket = socket
        self.read_buffer = RingBuffer(2 ** 20)
        self.send_buffer = RingBuffer(2 ** 20)
        self.parser = MessageParser()

    def process_read_data(self):
        while True:
            parsed = self.parser.try_parse(self.read_buffer)
            if parsed is None:
                return
            else:
                self.received_message(*parsed)

    def received_message(self, tid, message):
        print("received message", tid, message)
        if "m" not in message:
            print("unrecognized message, tid: {}  message: {}".format(tid, message))
            return
        method = message["m"]

        if method == "ping":
            self.queue_message(tid, {"m": "pong", "c": message["c"]})
        else:
            print("unrecognized message method:", method)

    def queue_message(self, tid, message):
        print("queuing message to client, tid: {}  message: {}".format(tid, message))
        data = bson.dumps(message)
        self.send_buffer.write(struct.pack(networking.MSG_HEADER_FMT, tid, len(data)))
        self.send_buffer.write(data)


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
                s
                for s, c in self.known_clients.items()
                if c.send_buffer.bytes_used() > 0
            ]
            if sockets_needing_writes:
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
                    self.known_clients[client_socket] = Client(client_socket)
                    self.handle_readable_socket(client_socket)
                else:
                    self.handle_readable_socket(sock)

    def handle_errored_socket(self, sock):
        print("socket in error", socket)
        del self.known_clients[sock]

    def handle_writable_socket(self, sock):
        if sock not in self.known_clients:
            return

        client = self.known_clients[sock]
        while True:
            to_send = client.send_buffer.read()
            if to_send is None:
                break
            print("sending {} bytes to {}".format(len(to_send), sock))
            try:
                networking.send_raw(sock, to_send)
            except RuntimeError:
                print("error sending, probably socket connection broke", sock)
                del self.known_clients[sock]
                return

    def handle_readable_socket(self, sock):
        if sock not in self.known_clients:
            return

        bytes_read = sock.recv(2048)
        if len(bytes_read) == 0:
            print("socket connection broken", sock)
            del self.known_clients[sock]
            return
        print("read {} bytes from {}".format(len(bytes_read), sock))

        client = self.known_clients[sock]
        try:
            client.read_buffer.write(bytes_read)
        except ValueError:
            print("client read buffer is full; disconnecting socket", sock)
            sock.close()
            del self.known_clients[sock]
            return

        client.process_read_data()


if __name__ == "__main__":
    Server().serve()
