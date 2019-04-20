import socket
import struct

s = socket.socket()
s.connect(('localhost', 4242))
s.send(struct.pack('>I', 32))
s.send('0' * 32)
while True:
    data = s.recv(1024)
    if not data: break
    print(repr(data))