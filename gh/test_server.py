#!/bin/env python3.9
import json
import socket
import logging
import struct
from typing import Literal, Sequence

import clingo


def send(s: socket.socket, payload: dict):
    message = json.dumps(payload)
    message_enc = message.encode('utf-8')
    message_len = len(message_enc)
    print(f"Sending payload of {message_len + 4} bytes.")
    header = struct.pack("<I", message_len)
    sent = s.send(header + message_enc)
    print(f"Sent {sent}/{message_len + 4} bytes.")
    return sent


def receive(s: socket.socket, buffer_size=1024):
    chunks = []
    header = s.recv(4)
    message_len = struct.unpack("<I", header)[0]
    received = 0
    while received < message_len:
        print("Receiving part of message.")
        message = s.recv(buffer_size)
        partial_message_len = len(message)
        received += partial_message_len
        print(f"Received {received}/{message_len} bytes.")
        if partial_message_len == 0:
            break
        message_dec = message.decode('utf-8')
        chunks.append(message_dec)
    print("Received whole message.")
    message = "".join(chunks)
    return json.loads(message)


def symbol_to_dict(symbol: clingo.Symbol):
    if symbol.type == clingo.SymbolType.Function:
        return {
            "name": symbol.name,
            "arguments": symbols_to_dict(symbol.arguments),
            "positive": symbol.positive
        }
    elif symbol.type == clingo.SymbolType.Number:
        return symbol.number
    elif symbol.type == clingo.SymbolType.String:
        return symbol.string


def symbols_to_dict(symbols: Sequence[clingo.Symbol]):
    return [symbol_to_dict(symbol) for symbol in symbols]


def solve(program):
    ctl = clingo.Control("0")
    ctl.add("base", [], program)
    ctl.ground((("base", []),))
    solve_result_str = "UNKOWN"
    nr_of_models = 0
    models = []
    exhausted = False
    with ctl.solve(yield_=True) as solve_handler:
        for model in solve_handler:
            nr_of_models += 1
            models.append(model.symbols(atoms=True))
        solve_result = solve_handler.get()
        exhausted = solve_result.exhausted
        if solve_result.satisfiable:
            solve_result_str = "SAT"
        elif solve_result.unsatisfiable:
            solve_result_str = "UNSAT"

    nr_of_models_str = "{}{}".format(nr_of_models, '+' if not exhausted else '')
    payload = {"Solve Result": solve_result_str, "Models": nr_of_models}
    for i, model in enumerate(models):
        payload[i + 1] = symbols_to_dict(model)

    return payload


def listen(port=8008, backlog=5):
    print(f"Starting socket on port {port} with a queue of {backlog}.")
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Created socket.")
    serversocket.bind((socket.gethostname(), port))
    print("Bound socket.")
    serversocket.listen(backlog)
    print("Listening.")
    return serversocket


def process_request(request):
    print(request)
    return solve(f"cylinderHeight({request['request'] + 10}). serialNr_obj(1, 1). serialNr_obj(2, 2). -holds(a). holds(-b).")


def main():
    serversocket = listen()

    while True:
        try:
            print("Waiting for new requests.")
            (clientsocket, address) = serversocket.accept()
            print("Received request.")
            request = receive(clientsocket)
            print("Processed request.")
            payload = process_request(request)
            send(clientsocket, payload)
        except KeyboardInterrupt:
            break
        except InterruptedError:
            break

    print("Closing server socket.")
    serversocket.close()


if __name__ == '__main__':
    main()
