#!/bin/env python2.7
import contextlib
import os.path
import socket
import json
import struct

if 'x' not in locals():
    print("[ Info]: x is None")
    global x
    x = None
else:
    print("[Debug]: x is {}".format(x))
if 'y' not in locals():
    print("[ Info]: y is None")
    global y
    y = None
else:
    print("[Debug]: y is {}".format(y))
a = None


def send(s, message):
    print "[ Info]: Sending message {}.".format(message)
    payload = json.dumps(message)
    payload_enc = payload.encode('utf-8')
    payload_len = len(payload_enc)
    print "[Debug]: Sending payload of {} bytes.".format(payload_len + 4)
    header = struct.pack("<I", payload_len)
    sent = s.send(header + payload_enc)
    print "[Debug]: Sent {}/{} bytes.".format(sent, payload_len + 4)
    return sent


def receive(s, buffer_size=1024):
    header_received = 0
    header_chunks = []
    while header_received < 4:
        print "[Debug]: Receiving header."
        header_chunk = s.recv(4 - header_received)
        header_chunk_len = len(header_chunk)
        header_chunks.append(header_chunk)
        header_received += header_chunk_len
        print "[Debug]: Received {}/4 bytes of header".format(header_received)
        if header_chunk_len == 0:
            raise Exception("Did not receive any further header data.")

    print "[Debug]: Received full header."
    header = bytes().join(header_chunks)
    message_len = struct.unpack("<I", header)[0]

    print "[ Info]: Receiving {} bytes of payload.".format(message_len)
    received = 0
    chunks = []
    while received < message_len:
        print "[Debug]: Receiving part of payload."
        message = s.recv(buffer_size)
        partial_message_len = len(message)
        received += partial_message_len
        print "[Debug]: Received {}/{} bytes.".format(received, message_len)
        if partial_message_len == 0:
            break
        message_dec = message.decode('utf-8')
        chunks.append(message_dec)
    print "[Debug]: Received all {} bytes.".format(message_len)
    message_str = "".join(chunks)
    message = json.loads(message_str)
    print "[ Info]: Received {}".format(message)
    return message


def symbol_to_str(symbol):
    if isinstance(symbol, dict):
        if "name" in symbol:
            out_str = ""
            name = symbol["name"]
            positive = symbol.get("positive", True)
            arguments = symbol.get("arguments", [])
            if not positive:
                out_str = "¬"
            out_str += name
            if not arguments:
                return out_str
            out_str += "{}{}{}".format('(', ",".join(symbol_to_str(argument) for argument in arguments), ')')
            return out_str
    elif isinstance(symbol, int):
        return str(symbol)


def process_answer(answer):
    if not answer:
        return None
    solve_result = answer["Solve Result"]  # type: str
    nr_of_models = answer["Models"]  # type: str
    nm = nr_of_models
    if nr_of_models.endswith('+'):
        nm = nr_of_models[0:-1]
    ms = int(nm)
    ret = [answer, solve_result, nr_of_models]
    models = []
    for m in range(1, ms + 1):
        models.append(answer[str(m)])
    for i, model in enumerate(models):
        ret.append("Model {}: {}".format(i + 1, len(model)))
        for symbol in model:
            ret.append(symbol_to_str(symbol))
    return ret


def connect(port=8008):
    print "[ Info]: Connecting to port {}.".format(port)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "[Debug]: Created socket."
    clientsocket.connect((socket.gethostname(), port))
    print "[Debug]: Connected."
    return clientsocket


def main():
    global x
    global y
    s = connect()
    with contextlib.closing(s) as clientsocket:
        message = {}
        if x is not None:
            message["programs"] = x
        if y is not None:
            message["clingo_args"] = y
        send(clientsocket, message)
        answer = receive(clientsocket)
        global a
        a = process_answer(answer)
        print "[ Info]: Closing socket."


if __name__ == "__main__":
    main()
