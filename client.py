import socket
import time

import networking


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 8000))

    counter = 0
    while True:
        tid = 1
        message = {"m": "ping", "c": counter}
        print("sending message:", tid, message)
        networking.send_msg(s, tid, message)

        tid_in, reply = networking.recv_msg(s)
        print("received reply:", tid_in, reply)

        time.sleep(1)
        counter += 1


if __name__ == "__main__":
    main()
