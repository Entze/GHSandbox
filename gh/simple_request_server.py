#!/bin/env python3.9
import contextlib
import json
import os
import socket
import logging
import struct
from pathlib import Path
from typing import Literal, Sequence, Union, Optional

import clingo


def send(s: socket.socket, message: dict):
    print(f"[ Info]: Sending message {message}.")
    payload = json.dumps(message)
    payload_enc = payload.encode('utf-8')
    payload_len = len(payload_enc)
    print(f"[Debug]: Sending payload of {payload_len + 4} bytes.")
    header = struct.pack("<I", payload_len)
    sent = s.send(header + payload_enc)
    print(f"[Debug]: Sent {sent}/{payload_len + 4} bytes.")
    return sent


def receive(s: socket.socket, buffer_size=1024):
    header_received = 0
    header_chunks = []
    while header_received < 4:
        print("[Debug]: Receiving header.")
        header_chunk = s.recv(4 - header_received)
        header_chunk_len = len(header_chunk)
        header_chunks.append(header_chunk)
        header_received += header_chunk_len
        print(f"[Debug]: Received {header_received}/4 bytes of header.")
        if header_chunk_len == 0:
            raise Exception("Did not receive any further header data.")
    print("[Debug]: Received full header.")
    header = bytes().join(header_chunks)
    message_len = struct.unpack("<I", header)[0]

    print(f"[ Info]: Receiving {message_len} bytes of payload.")
    received = 0
    chunks = []
    while received < message_len:
        print("[Debug]: Receiving part of message.")
        message = s.recv(buffer_size)
        partial_message_len = len(message)
        received += partial_message_len
        print(f"[Debug]: Received {received}/{message_len} bytes.")
        if partial_message_len == 0:
            break
        message_dec = message.decode('utf-8')
        chunks.append(message_dec)
    print(f"[Debug]: Received all {message_len} bytes.")
    message_str = "".join(chunks)
    message = json.loads(message_str)
    print(f"[ Info]: Received {message}")
    return message


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


def add_program(ctl: clingo.Control, program: Union[str, Path], name: str = "base",
                parameters: Optional[Sequence[str]] = None):
    if isinstance(program, Path):
        ctl.load(str(program.absolute()))
    elif isinstance(program, str):
        if os.path.isfile(program):
            ctl.load(program)
        else:
            ctl.add(name, parameters or [], program)


def solve(programs=None, clingo_args=('--models', '1')):
    if programs is None:
        return {}
    ctl = clingo.Control(clingo_args)
    if isinstance(programs, str) or isinstance(programs, Path):
        add_program(ctl, programs)
    elif isinstance(programs, Sequence):
        for program in programs:
            add_program(ctl, program)

    ctl.ground((("base", []),))
    solve_result_str = "UNKOWN"
    nr_of_models = 0
    models = []
    with ctl.solve(yield_=True) as solve_handler:
        for model in solve_handler:
            nr_of_models += 1
            models.append(model.symbols(shown=True))
        solve_result = solve_handler.get()
        exhausted = solve_result.exhausted
        if solve_result.satisfiable:
            solve_result_str = "SAT"
        elif solve_result.unsatisfiable:
            solve_result_str = "UNSAT"

    nr_of_models_str = "{}{}".format(nr_of_models, '+' if not exhausted else '')
    payload = {"Solve Result": solve_result_str, "Models": nr_of_models_str}
    for i, model in enumerate(models):
        payload[i + 1] = symbols_to_dict(model)

    return payload


def listen(port=8008, backlog=5):
    print(f"[ Info]: Starting socket on port {port} with a queue of {backlog}.")
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("[Debug]: Created socket.")
    serversocket.bind((socket.gethostname(), port))
    print("[Debug]: Bound socket.")
    serversocket.listen(backlog)
    print("[Debug]: Listening.")
    return serversocket


def process_request(request):
    return solve(**request)


def main():
    s = listen()
    with contextlib.closing(s) as serversocket:
        stop = False
        while not stop:
            try:
                print("[Debug]: Waiting for new requests.")
                (clientsocket, address) = serversocket.accept()
                print("[Debug]: Received request.")
                request = receive(clientsocket)
                print("[Debug]: Processed request.")
                payload = process_request(request)
                send(clientsocket, payload)
            except (KeyboardInterrupt, InterruptedError):
                stop = True
        print("[ Info]: Closing socket.")


if __name__ == '__main__':
    main()
