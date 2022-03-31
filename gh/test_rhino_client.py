#!/bin/env python2.7
import socket
import json
import struct

import Rhino
import scriptcontext
import System.Guid


def add_cylinder(radius=5, height=10):
    center_point = Rhino.Geometry.Point3d(0, 0, 0)
    height_point = Rhino.Geometry.Point3d(0, 0, height)
    zaxis = height_point - center_point
    plane = Rhino.Geometry.Plane(center_point, zaxis)
    circle = Rhino.Geometry.Circle(plane, radius)
    cylinder = Rhino.Geometry.Cylinder(circle, zaxis.Length)
    brep = cylinder.ToBrep(True, True)
    if brep:
        if scriptcontext.doc.Objects.AddBrep(brep) != System.Guid.Empty:
            scriptcontext.doc.Views.Redraw()
            return Rhino.Commands.Result.Success
    return Rhino.Commands.Result.Failure


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
            cylinder_height = 10
    add_cylinder(cylinder_height)


def connect(port=8008):
    print "Connecting to port {}.".format(port)
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print "Created socket."
    clientsocket.connect((socket.gethostname(), port))
    print "Connected."
    return clientsocket


def main():
    clientsocket = connect()

    print "Send message."
    send(clientsocket, {"request": "0"})
    message = receive(clientsocket)
    process_answer(message)
    clientsocket.close()
    print "Closed socket."



if __name__ == "__main__":
    main()
