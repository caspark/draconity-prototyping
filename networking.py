import struct

import bson

from ring_buffer import RingBuffer

MSG_HEADER_FMT = "!QQ"  # transaction_id, data_length


class MessageReader(object):
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
        self._read_buffer = RingBuffer(2 ** 20)
        self._send_buffer = RingBuffer(2 ** 20)
        self._parser = MessageReader()

    def debug(self, s):
        print("Messenger{}: {}".format(self.socket.getpeername(), s))

    def read_messages(self):
        """Call this you when know there is readable data for this socket;
        it will yield a tuple in the format of (transaction_id, message object)
        for each message that has been received."""
        bytes_read = self.socket.recv(2048)
        if len(bytes_read) == 0:
            raise MessengerConnectionBroken("Socket connection broken", self.socket)
        self.debug("read {} bytes".format(len(bytes_read)))

        try:
            self._read_buffer.write(bytes_read)
        except ValueError:
            raise MessengerBufferFullError(
                "Failed to read message because read buffer is full", self.socket
            )

        while True:
            parsed = self._parser.try_parse(self._read_buffer)
            if parsed is None:
                return
            else:
                (tid, message) = parsed
                self.debug(
                    "received message; tid: {}  message: {}".format(tid, message)
                )
                yield tid, message

    def queue_message(self, tid, message):
        """An API for queuing messages for sending later"""
        self.debug("queuing message; tid: {}  message: {}".format(tid, message))
        data = bson.dumps(message)
        header = struct.pack(MSG_HEADER_FMT, tid, len(data))
        try:
            self._send_buffer.write(header)
            self._send_buffer.write(data)
        except ValueError:
            MessengerBufferFullError(
                "Failed to enqueue message because send buffer is full", self.socket
            )

    def has_messages_to_send(self):
        """Returns true if a message was previously queued but has not yet been sent"""
        return self._send_buffer.bytes_used() > 0

    def send_messages(self):
        """Call this to actually send messages previous queued"""
        while True:
            to_send = self._send_buffer.read()
            if to_send is None:
                break
            self.debug("sending {} bytes".format(len(to_send)))

            message_length = len(to_send)
            bytes_sent_total = 0
            while bytes_sent_total < message_length:
                sent = self.socket.send(to_send[bytes_sent_total:])
                if sent == 0:
                    raise MessengerConnectionBroken(
                        "error sending, probably socket connection broke", self.socket
                    )
                bytes_sent_total += sent
