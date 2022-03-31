#!/bin/env python2.7
import socket
import json
import struct

def process_answer(clientsocket):
    answer_size_bytes = clientsocket.recv(4)
    answer_size = struct.unpack("<I", answer_size_bytes)[0]
    print "Will receive answer of size {}.".format(answer_size)
    answer_bytes = clientsocket.recv(answer_size)
    print "Received {}/{} bytes.".format(len(answer_bytes), answer_size)
    answer = struct.unpack("<s", answer_bytes)
    print type(answer)
    print answer

def prepare_message():
    message = bytes()
    msg_len = 4
    message = message.join(struct.pack('<I', 0))
    return message, msg_len


def connect(port=8008):
    print "Connecting to port {}.".format(port)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "Created socket."
    clientsocket.connect((socket.gethostname(), port))
    print "Connected."
    return clientsocket


def main():
    clientsocket = connect()

    print "Prepare message."
    (message, msg_len) = prepare_message()
    print "Send message."
    sent = clientsocket.send(message)
    print "Sent {}/{} bytes.".format(sent, msg_len)
    answer = process_answer(clientsocket)
    clientsocket.close()
    print "Closed socket."


if __name__ == "__main__":
    main()
