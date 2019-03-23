import struct
import bson


def recv_msg(sock):
    length = struct.unpack("!Q", _recv_raw(sock, 8))[0]
    message_bytes = _recv_raw(sock, length)
    return bson.loads(message_bytes)


def _recv_raw(sock, message_length):
    chunks = []
    bytes_received = 0
    while bytes_received < message_length:
        # TODO - why limit chunk size here?
        chunk = sock.recv(min(message_length - bytes_received, 2048))
        if chunk == b"":
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_received = bytes_received + len(chunk)
    return b"".join(chunks)


def send_msg(sock, obj):
    data = bson.dumps(obj)
    _send_raw(sock, struct.pack("!Q", len(data)))
    _send_raw(sock, data)


def _send_raw(sock, data):
    message_length = len(data)
    bytes_sent_total = 0
    while bytes_sent_total < message_length:
        sent = sock.send(data[bytes_sent_total:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        bytes_sent_total += sent
