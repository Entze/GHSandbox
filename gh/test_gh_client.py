#!/bin/env python2.7
import socket
import json
import struct

a = None

def send(s, payload):
    message = json.dumps(payload)
    message_enc = message.encode('utf-8')
    message_len = len(message_enc)
    print "Sending payload of {} bytes.".format(message_len + 4)
    header = struct.pack("<I", message_len)
    sent = s.send(header + message_enc)
    print "Sent {}/{} bytes.".format(sent, message_len + 4)
    return sent


def receive(s, buffer_size=1024):
    chunks = []
    header = s.recv(4)
    message_len = struct.unpack("<I", header)[0]
    received = 0
    while received < message_len:
        print "Receiving part of message."
        message = s.recv(buffer_size)
        partial_message_len = len(message)
        received += partial_message_len
        print "Received {} bytes.".format(received)
        if partial_message_len == 0:
            break
        message_dec = message.decode('utf-8')
        chunks.append(message_dec)
    print "Received whole message."
    message = "".join(chunks)
    return json.loads(message)


def process_answer(message):
    print message
    cylinder_height = 0
    for symbol in message["1"]:
        if symbol["name"] == "cylinderHeight":
            cylinder_height = symbol["arguments"][0]
    return cylinder_height


def connect(port=8008):
    print "Connecting to port {}.".format(port)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "Created socket."
    clientsocket.connect((socket.gethostname(), port))
    print "Connected."
    return clientsocket


def main():
    global x
    clientsocket = connect()

    print "Send message."
    send(clientsocket, {"request": x})
    message = receive(clientsocket)
    global a
    a = process_answer(message)
    clientsocket.close()
    print "Closed socket."


if __name__ == "__main__":
    main()
