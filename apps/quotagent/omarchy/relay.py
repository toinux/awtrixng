#!/usr/bin/env python3
"""Publish Omarchy's Codex quota windows to MQTT."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def payload(record):
    limits = record.get("limits") if isinstance(record, dict) else None
    # The cache drops the numeric duration and adds a title only for model-specific limits.
    durations = {"5h window": 18000, "Weekly (7-day)": 604800}
    slots = dict.fromkeys(durations)
    if isinstance(limits, list):
        for item in limits:
            if not isinstance(item, dict) or "title" in item:
                continue
            label = item.get("label")
            percent = item.get("percent")
            if not isinstance(label, str) or label not in slots:
                continue
            if isinstance(percent, bool) or not isinstance(percent, (int, float)) or not 0 <= percent <= 1:
                continue
            reset = item.get("resetsAt")
            try:
                parsed = datetime.fromisoformat(reset.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                reset = int(parsed.timestamp())
            except (AttributeError, TypeError, ValueError, OverflowError):
                continue
            slots[label] = {
                "durationSeconds": durations[label],
                "remainingPercent": round((1 - percent) * 100, 10),
                "resetAt": reset,
            }
    return {"windows": list(slots.values())}


def main():
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    source = state / "omarchy/agents/usage/codex.json"
    try:
        result = payload(json.loads(source.read_text()))
    except (OSError, UnicodeError, ValueError):
        result = {"windows": [None, None]}
    command = ["mosquitto_pub", "-h", os.environ.get("MQTT_HOST", "localhost"),
               "-p", os.environ.get("MQTT_PORT", "1883"), "-t",
               os.environ.get("MQTT_TOPIC", "quotagent/status"), "-q", "1", "-r", "-s"]
    subprocess.run(command, input=json.dumps(result, separators=(",", ":")),
                   text=True, check=True, capture_output=True, timeout=10)


def entrypoint():
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(f"quotagent MQTT relay failed (exit {error.returncode})", file=sys.stderr)
        return 1
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"quotagent MQTT relay failed ({error.__class__.__name__})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(entrypoint())
