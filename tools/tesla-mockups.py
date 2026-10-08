#!/usr/bin/env python3
"""Exercise the real Tesla renderer on AWTRIX using an isolated temporary app."""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parent.parent
APP = "TeslaMock"
spec = importlib.util.spec_from_file_location("awtrix_screen", ROOT / "tools/awtrix-screen.py")
assert spec is not None and spec.loader is not None
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
spec = importlib.util.spec_from_file_location("mqtt_read", ROOT / "tools/mqtt-read.py")
assert spec is not None and spec.loader is not None
mqtt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mqtt)

# name, SOC, limit, charging state, power, displayed page
CASES = [
    ("missing", None, None, "Disconnected", None, "battery"),
    ("disconnected", "74", "80", "Disconnected", "22", "battery"),
    ("plugged-stopped", "74", "80", "Stopped", "22", "battery"),
    ("complete-100", "100", "100", "Complete", "0", "battery"),
    ("charging-battery", "74", "80", "Charging", "11", "battery"),
    ("charging-11kw", "74", "80", "Charging", "11", "power"),
    ("charging-7_4kw", "74", "80", "Charging", "7.4", "power"),
    ("charging-250kw", "20", "80", "Charging", "250", "power"),
    ("charging-zero", "74", "80", "Charging", "0", "power"),
    ("charging-invalid", "74", "80", "Charging", "invalid", "power"),
    ("charging-negative", "74", "80", "Charging", "-1", "power"),
]


def mock_source(source, fields, topic):
    # Use production settings as diagnostic defaults, without modifying its store.
    for field in fields:
        value = field["value"]
        encoded = json.dumps(value, ensure_ascii=False)
        pattern = r'(?m)^(# @config ' + re.escape(field["key"]) + r'\s+.*?default=)("[^"]*"|\S+)'
        source = re.sub(pattern, lambda match: match[1] + encoded, source)
    source = re.sub(r"(?m)^# @name .*", "# @name " + APP, source)
    source = source.replace("import math", "import math\nimport json")
    source = source.replace("class Tesla", "class Tesla\n  var mock_power_page")
    source = source.replace("mqtt.subscribe(", "self.mock_subscribe(")
    source = source.replace(
        "self.shown_at = now_ms()",
        "self.shown_at = now_ms() - (self.mock_power_page ? self.page : 0)",
    )
    hooks = '''
  def mock_subscribe(topic, callback)
  end
  def setup()
    self.mock_power_page = false
    mqtt.subscribe(TOPIC, / t, p -> self.set_mock(p))
  end
  def set_mock(payload)
    var values = json.load(payload)
    self.set_battery(values[0])
    self.set_limit(values[1])
    self.set_charging(values[2])
    self.set_power(values[3])
    self.mock_power_page = values[4] == "power"
    self.on_show()
  end
'''.replace("TOPIC", json.dumps(topic))
    marker = r"\nend\s*\nreturn Tesla\(\)\s*$"
    source, count = re.subn(marker, lambda _: hooks + "\nend\n\nreturn Tesla()\n", source)
    if count != 1:
        raise RuntimeError("Cannot locate Tesla class ending for diagnostic hooks")
    return source


def connect_mock_broker(system):
    if not system.get("mqttEnabled") or not system.get("mqttHost"):
        raise RuntimeError("AWTRIX MQTT broker is not configured")
    username, password = system.get("mqttUser") or "", system.get("mqttPass") or ""
    flags = 0x02 | (0x80 if username else 0) | (0x40 if password else 0)
    body = b"\x00\x04MQTT\x04" + bytes((flags,)) + struct.pack(">H", 30)
    body += mqtt.mqtt_string("tesla-mock-" + uuid.uuid4().hex[:12])
    if username:
        body += mqtt.mqtt_string(username)
    if password:
        body += mqtt.mqtt_string(password)
    sock = socket.create_connection((system["mqttHost"], int(system.get("mqttPort", 1883))), timeout=8)
    try:
        sock.sendall(mqtt.packet(0x10, body))
        kind, body = mqtt.read_packet(sock)
        if kind >> 4 != 2 or len(body) != 2 or body[1] != 0:
            raise RuntimeError("MQTT broker refused diagnostic connection")
        return sock
    except BaseException:
        sock.close()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="/tmp/opencode/tesla-mockups")
    parser.add_argument("--case", choices=[case[0] for case in CASES], action="append")
    args = parser.parse_args()
    ip = screen.config_value("AWTRIX_IP")
    if not ip:
        parser.error("AWTRIX_IP is not configured")
    base = "http://" + ip.rstrip("/") + "/api/v1/"
    auth = screen.config_value("AWTRIX_AUTH")

    def api(path, data=None, method=None, content_type="application/json"):
        return json.loads(screen.request(base, path, auth, data, method, content_type))

    if any(app["name"] == APP for app in api("apps")):
        raise SystemExit(APP + " already exists; refusing to replace it")
    previous_app = api("device").get("currentApp")
    fields = api("apps/Tesla/config")["fields"]
    system = api("system")
    source = (ROOT / "tesla.ax").read_text()
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=True)
    installed = False
    captures = []
    cycle_frame = None
    settings = {field["key"]: field["value"] for field in fields}
    topic = "awtrixng/mock/tesla/" + uuid.uuid4().hex
    try:
        with tempfile.TemporaryDirectory(dir="/tmp/opencode") as temporary, connect_mock_broker(system) as sock:
            path = Path(temporary) / "tesla-mock.ax"
            path.write_text(mock_source(source, fields, topic))
            result = subprocess.run(
                [str(ROOT / "minify-berry/minify-berry.ts"), "--classes", "--variables", str(path)],
                check=True, capture_output=True,
            )
            reply = api("apps/script/" + APP, result.stdout, "PUT", "text/plain")
            installed = True
            if "error" not in reply or reply["error"] is not None:
                raise RuntimeError(f"Diagnostic install failed: {reply}")
            time.sleep(0.5)
            for case in CASES:
                if args.case and case[0] not in args.case:
                    continue
                # QoS 0, non-retained, UUID topic: production TeslaMate topics are untouched.
                sock.sendall(mqtt.packet(0x30, mqtt.mqtt_string(topic) + json.dumps(case[1:]).encode()))
                time.sleep(0.35)
                pinned = api("apps/active", json.dumps({"name": APP, "fast": True}).encode(), "PUT")
                if not pinned.get("ok"):
                    raise RuntimeError("Cannot show diagnostic app: " + str(pinned))
                time.sleep(0.25)
                frame = api("display/screen")
                if api("device").get("currentApp") != APP:
                    raise RuntimeError("Diagnostic app is no longer active")
                app = next(app for app in api("apps") if app["name"] == APP)
                if app.get("error") is not None:
                    raise RuntimeError(f"{case[0]} runtime error: {app['error']}")
                w, h, pixels = frame["width"], frame["height"], frame["pixels"]
                if len(pixels) != w * h or not any(pixels[:w * (h - 1)]):
                    raise RuntimeError(f"{case[0]} incomplete or blank display")
                expected_bar = [settings["bg"]] * w
                if case[2] is not None:
                    count = min(w, max(0, int(float(case[2]) * w / 100 + 0.5)))
                    expected_bar[:count] = [settings["lc"]] * count
                if case[1] is not None:
                    count = min(w, max(0, int(float(case[1]) * w / 100 + 0.5)))
                    color = settings["cc"] if case[3] == "Charging" else settings["bc"]
                    expected_bar[:count] = [color] * count
                if pixels[-w:] != expected_bar:
                    raise RuntimeError(f"{case[0]} incorrect SOC / charge-limit bar")
                (output / (case[0] + ".json")).write_text(json.dumps(frame))
                screen.write_png(output / (case[0] + ".png"), w, h, pixels, 12)
                captures.append(frame)
                print(f"{case[0]}: error=null, {w}x{h}, {output / (case[0] + '.png')}")
                if case[0] == "charging-battery":
                    # Remain in the SAME dwell: repinning would reset on_show and the page timer.
                    time.sleep(settings.get("page", 3) + 0.1)
                    if api("device").get("currentApp") != APP:
                        raise RuntimeError("Diagnostic dwell ended before the power page")
                    cycle_frame = api("display/screen")
                    screen.write_png(output / "automatic-power.png", w, h, cycle_frame["pixels"], 12)
                if case[0] == "charging-11kw" and cycle_frame is not None:
                    # Exclude the animated plug and bar; both power pages must have identical text.
                    text_pixels = lambda frame: [
                        frame["pixels"][y * w + x] for y in range(h - 1) for x in range(w - 9)
                    ]
                    if text_pixels(cycle_frame) != text_pixels(frame):
                        raise RuntimeError("Automatic alternation did not reach the expected 11kW page")
                    print("automatic alternation: battery -> 11kW verified")
            sock.sendall(mqtt.packet(0xE0))
        if captures:
            w, h = captures[0]["width"], captures[0]["height"]
            pixels = []
            for frame in captures:
                if (frame["width"], frame["height"]) != (w, h):
                    raise RuntimeError("Display dimensions changed during capture")
                pixels.extend(frame["pixels"])
                pixels.extend([0] * w * 2)
            screen.write_png(output / "all.png", w, (h + 2) * len(captures), pixels, 12)
            print("Contact sheet (same order as above): " + str(output / "all.png"))
    finally:
        if installed:
            api("apps/" + APP, method="DELETE")
        if previous_app:
            api("apps/active", json.dumps({"name": previous_app, "fast": True}).encode(), "PUT")


if __name__ == "__main__":
    main()
