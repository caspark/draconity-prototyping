import socket
import time

import networking


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((socket.gethostname(), 8000))

    counter = 0
    while True:
        message = f"ping {counter}"
        print("sending message:", message)
        networking.send_msg(s, message)
        reply = networking.recv_msg(s)
        print("received reply:", reply)

        time.sleep(1)
        counter += 1


if __name__ == "__main__":
    main()
