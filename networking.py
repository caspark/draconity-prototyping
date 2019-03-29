import struct
import bson

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
