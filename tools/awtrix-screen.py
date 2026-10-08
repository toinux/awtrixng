#!/usr/bin/env python3
"""Capture the AWTRIX framebuffer as a small, readable PNG."""

import argparse
import base64
import json
import os
from pathlib import Path
import struct
import time
import urllib.error
import urllib.request
import zlib


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


def request(base, path, auth, data=None, method=None, content_type="application/json"):
    headers = {}
    if data is not None:
        headers["Content-Type"] = content_type
    if auth:
        token = base64.b64encode(auth.encode()).decode()
        headers["Authorization"] = "Basic " + token
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()


def png_chunk(kind, payload):
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_png(path, width, height, pixels, scale):
    scaled_width = width * scale
    scaled_height = height * scale
    rows = bytearray()
    for y in range(height):
        row = bytearray()
        for x in range(width):
            color = pixels[y * width + x]
            rgba = bytes(((color >> 16) & 255, (color >> 8) & 255, color & 255, 255))
            row.extend(rgba * scale)
        for _ in range(scale):
            rows.append(0)
            rows.extend(row)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", struct.pack(">IIBBBBB", scaled_width, scaled_height, 8, 6, 0, 0, 0))
    data += png_chunk(b"IDAT", zlib.compress(bytes(rows)))
    data += png_chunk(b"IEND", b"")
    Path(path).write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", help="pin this app before capturing")
    parser.add_argument("--wait", type=float, default=0, help="seconds to wait after pinning")
    parser.add_argument("--scale", type=int, default=8, help="nearest-neighbour display scale")
    parser.add_argument("--out", default="/tmp/awtrix-screen.png", help="PNG output path")
    args = parser.parse_args()

    ip = config_value("AWTRIX_IP")
    if not ip:
        parser.error("AWTRIX_IP is not set in the environment or project .env")
    base = "http://" + ip.rstrip("/") + "/api/v1/"
    auth = config_value("AWTRIX_AUTH")

    if args.app:
        body = json.dumps({"name": args.app, "fast": True}).encode()
        result = json.loads(request(base, "apps/active", auth, body, method="PUT"))
        if not result.get("ok"):
            raise SystemExit("AWTRIX refused to pin app: " + json.dumps(result))
        if args.wait > 0:
            time.sleep(args.wait)

    screen = json.loads(request(base, "display/screen", auth))
    width, height = screen["width"], screen["height"]
    pixels = screen["pixels"]
    if len(pixels) != width * height:
        raise SystemExit("AWTRIX returned an incomplete framebuffer")
    write_png(args.out, width, height, pixels, max(1, args.scale))
    print(f"{args.out} ({width}x{height}, scaled {max(1, args.scale)}x)")


if __name__ == "__main__":
    main()
