#!/bin/env python3.9
import json
import socket
import logging
import struct
from typing import Literal


def solve():
    pass


def prepare_answer(answer: dict, byteorder: Literal['little', 'big'] = 'little'):
    answer_json_str = json.dumps(answer)
    answer_bytes = bytes(answer_json_str, 'ascii')
    answer_size = len(answer_bytes)
    answer_bytes = struct.pack("<Is", answer_size, answer_bytes)
    return answer_bytes, answer_size


def process(clientsocket, byteorder: Literal['little', 'big'] = 'little'):
    request_size_bytes: bytes = clientsocket.recv(4)
    request_size = int.from_bytes(request_size_bytes, byteorder)
    print(f"Will receive {request_size} bytes.")


def listen(port=8008, backlog=5):
    print(f"Starting socket on port {port} with a queue of {backlog}.")
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Created socket.")
    serversocket.bind((socket.gethostname(), port))
    print("Bound socket.")
    serversocket.listen(backlog)
    print("Listening.")
    return serversocket


def main():
    serversocket = listen()

    while True:
        try:
            print("Waiting for new requests.")
            (clientsocket, address) = serversocket.accept()
            print("Received request.")
            process(clientsocket)
            print("Processed request.")
            print("Prepare answer.")
            answer, answer_size = prepare_answer({"answer sets": ["cylinder(10)"]})
            print("Sending answer.")
            sent = clientsocket.send(answer)
            print(f"Sent {sent}/{answer_size} bytes.")
        except KeyboardInterrupt:
            break
        except InterruptedError:
            break

    print("Closing server socket.")
    serversocket.close()


if __name__ == '__main__':
    main()
