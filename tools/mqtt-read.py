#!/usr/bin/env python3
"""Read retained MQTT topics using the broker configured on AWTRIX NG."""

import argparse
import base64
import json
import os
from pathlib import Path
import socket
import struct
import urllib.request


ROOT = Path(__file__).resolve().parent.parent


def config_value(name):
    value = os.environ.get(name)
    if value:
        return value
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


def encode_remaining_length(length):
    encoded = bytearray()
    while True:
        digit = length % 128
        length //= 128
        if length:
            digit |= 0x80
        encoded.append(digit)
        if not length:
            return bytes(encoded)


def packet(kind, body=b""):
    return bytes((kind,)) + encode_remaining_length(len(body)) + body


def read_exact(sock, length):
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("broker closed the connection")
        data.extend(chunk)
    return bytes(data)


def read_packet(sock):
    header = read_exact(sock, 1)[0]
    multiplier = 1
    remaining = 0
    while True:
        digit = read_exact(sock, 1)[0]
        remaining += (digit & 0x7F) * multiplier
        if not digit & 0x80:
            break
        multiplier *= 128
        if multiplier > 128**4:
            raise ValueError("invalid MQTT packet length")
    return header, read_exact(sock, remaining)


def awtrix_system():
    ip = config_value("AWTRIX_IP")
    if not ip:
        raise RuntimeError("AWTRIX_IP is not set in the environment or project .env")
    base = "http://" + ip.rstrip("/") + "/api/v1/"
    auth = config_value("AWTRIX_AUTH")
    headers = {}
    if auth:
        token = base64.b64encode(auth.encode()).decode()
        headers["Authorization"] = "Basic " + token
    request = urllib.request.Request(base + "system", headers=headers)
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.loads(response.read())


def mqtt_string(value):
    encoded = value.encode()
    return struct.pack(">H", len(encoded)) + encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--car-id", type=int, help="read TeslaMate topics for this car")
    parser.add_argument("--namespace", default="", help="optional TeslaMate topic namespace")
    parser.add_argument("--topic", action="append", default=[], help="topic to read (repeatable)")
    parser.add_argument("--timeout", type=float, default=6, help="seconds to wait for retained values")
    args = parser.parse_args()

    topics = list(args.topic)
    if args.car_id is not None:
        prefix = "teslamate/"
        if args.namespace:
            prefix += args.namespace.strip("/") + "/"
        prefix += "cars/" + str(args.car_id) + "/"
        topics.extend(prefix + field for field in (
            "battery_level", "charge_limit_soc", "charging_state", "charger_power", "state"
        ))
    if not topics:
        parser.error("provide --car-id or at least one --topic")

    system = awtrix_system()
    if not system.get("mqttEnabled"):
        raise SystemExit("MQTT is disabled in AWTRIX system configuration")
    host = system.get("mqttHost")
    port = int(system.get("mqttPort", 1883))
    if not host:
        raise SystemExit("AWTRIX system configuration has no MQTT broker host")

    client_id = "awtrixng-mqtt-read"
    username = system.get("mqttUser") or ""
    password = system.get("mqttPass") or ""
    flags = 0x02
    if username:
        flags |= 0x80
    if password:
        flags |= 0x40
    connect_body = b"\x00\x04MQTT\x04" + bytes((flags,)) + struct.pack(">H", 30)
    connect_body += mqtt_string(client_id)
    if username:
        connect_body += mqtt_string(username)
    if password:
        connect_body += mqtt_string(password)

    received = set()
    with socket.create_connection((host, port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        sock.sendall(packet(0x10, connect_body))
        kind, body = read_packet(sock)
        if kind >> 4 != 2 or len(body) != 2 or body[1] != 0:
            raise SystemExit("MQTT broker refused connection")

        subscriptions = struct.pack(">H", 1)
        for topic in dict.fromkeys(topics):
            subscriptions += mqtt_string(topic) + b"\x00"
        sock.sendall(packet(0x82, subscriptions))
        kind, body = read_packet(sock)
        if kind >> 4 != 9 or len(body) < 3 or any(code == 0x80 for code in body[2:]):
            raise SystemExit("MQTT broker refused one or more topic subscriptions")

        targets = set(topics)
        while received != targets:
            try:
                kind, body = read_packet(sock)
            except socket.timeout:
                break
            if kind >> 4 != 3 or len(body) < 2:
                continue
            topic_length = struct.unpack(">H", body[:2])[0]
            topic = body[2:2 + topic_length].decode(errors="replace")
            offset = 2 + topic_length
            qos = (kind >> 1) & 0x03
            packet_id = None
            if qos:
                packet_id = struct.unpack(">H", body[offset:offset + 2])[0]
                offset += 2
            payload = body[offset:]
            retained = bool(kind & 0x01)
            print(f"{topic} = {payload.decode(errors='replace')!r} (retained={retained})")
            received.add(topic)
            if qos == 1 and packet_id is not None:
                sock.sendall(packet(0x40, struct.pack(">H", packet_id)))
        sock.sendall(packet(0xE0))

    print(f"received {len(received)} of {len(targets)} requested topics")


if __name__ == "__main__":
    main()
