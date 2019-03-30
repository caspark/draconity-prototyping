import struct

import bson

from ring_buffer import RingBuffer

MSG_HEADER_FMT = "!QQ"  # transaction_id, data_length


def recv_msg(sock):
    transaction_id, length = struct.unpack(
        MSG_HEADER_FMT, _recv_raw(sock, struct.calcsize(MSG_HEADER_FMT))
    )
    message_bytes = _recv_raw(sock, length)
    return transaction_id, bson.loads(message_bytes)


def _recv_raw(sock, message_length):
    data = bytearray(message_length)
    offset = 0
    while offset < message_length:
        chunk = sock.recv(min(message_length - offset, 2048))
        if chunk == b"":
            raise RuntimeError("socket connection broken")
        new_offset = offset + len(chunk)
        data[offset:new_offset] = chunk
        offset = new_offset
    return data


def send_msg(sock, transaction_id, obj):
    data = bson.dumps(obj)
    send_raw(sock, struct.pack(MSG_HEADER_FMT, transaction_id, len(data)))
    send_raw(sock, data)


def send_raw(sock, data):
    message_length = len(data)
    bytes_sent_total = 0
    while bytes_sent_total < message_length:
        sent = sock.send(data[bytes_sent_total:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        bytes_sent_total += sent


class MessageParser(object):
    def __init__(self):
        self.tid = None
        self.len = None
        self.msg = None

    def try_parse(self, ring_buffer):
        header_size = struct.calcsize(MSG_HEADER_FMT)
        if self.tid is None and ring_buffer.bytes_used() >= header_size:
            self.tid, self.len = struct.unpack(
                MSG_HEADER_FMT, ring_buffer.read_exactly(header_size)
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


class MessengerConnectionBroken(Exception):
    def __init__(self, message, socket):
        super().__init__(message)
        self.socket = socket


class MessengerBufferFullError(Exception):
    def __init__(self, message, socket):
        super().__init__(message)
        self.socket = socket


class Messenger(object):
    def __init__(self, socket):
        self.socket = socket
        self.read_buffer = RingBuffer(2 ** 20)
        self.send_buffer = RingBuffer(2 ** 20)
        self.parser = MessageParser()

    def receive_data(self):
        """Call this you know there is readable data for this socket"""
        bytes_read = self.socket.recv(2048)
        if len(bytes_read) == 0:
            raise MessengerConnectionBroken("Socket connection broken", self.socket)
        print("read {} bytes from {}".format(len(bytes_read), self.socket))

        try:
            self.read_buffer.write(bytes_read)
        except ValueError:
            raise MessengerBufferFullError(
                "Failed to read message because read buffer is full", self.socket
            )

        while True:
            parsed = self.parser.try_parse(self.read_buffer)
            if parsed is None:
                return
            else:
                self.received_message(*parsed)

    def received_message(self, tid, message):
        """A callback for receiving a message, expected to be overridden by subclasses"""
        raise NotImplementedError("received message not implemented")

    def queue_message(self, tid, message):
        """An API for queuing messages for sending later"""
        print("queuing message; tid: {}  message: {}".format(tid, message))
        data = bson.dumps(message)
        header = struct.pack(MSG_HEADER_FMT, tid, len(data))
        try:
            self.send_buffer.write(header)
            self.send_buffer.write(data)
        except ValueError:
            MessengerBufferFullError(
                "Failed to enqueue message because send buffer is full", self.socket
            )

    def has_data_to_send(self):
        return self.send_buffer.bytes_used() > 0

    def send_data(self):
        while True:
            to_send = self.send_buffer.read()
            if to_send is None:
                break
            print("sending {} bytes to {}".format(len(to_send), self.socket))
            try:
                send_raw(self.socket, to_send)
            except RuntimeError:
                raise MessengerConnectionBroken(
                    "error sending, probably socket connection broke", self.socket
                )
