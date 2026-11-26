#!/usr/bin/env python3
"""Publish Codex quotas from Omarchy or OpenCode Quota to MQTT."""
import json
import os
import subprocess
import sys
import time
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


def opencode_snapshot(record, account=None):
    if record.get("version") != 3 or not isinstance(record.get("providers"), dict):
        return 0, None
    provider = record["providers"].get("openai")
    if not isinstance(provider, dict) or provider.get("status") != "ok":
        return 0, None
    fetched = provider.get("fetchedAt")
    entries = provider.get("entries")
    if type(fetched) is not int or fetched <= 0 or not isinstance(entries, list):
        return 0, None
    durations = {"openai.five_hour": 18000, "openai.weekly": 604800}
    slots = dict.fromkeys(durations)
    seen = set()
    accounts = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        row_id, label = entry.get("id"), entry.get("account")
        if not isinstance(row_id, str) or row_id not in slots or (account is not None and label != account):
            continue
        if row_id in seen or (label is not None and not isinstance(label, str)):
            return 0, None
        seen.add(row_id)
        accounts.add(label)
        percent, reset = entry.get("percentRemaining"), entry.get("resetAt")
        if (entry.get("renderType") == "percent" and type(percent) in (int, float)
                and 0 <= percent <= 100 and type(reset) is int and reset > 0):
            slots[row_id] = {
                "durationSeconds": durations[row_id], "remainingPercent": percent, "resetAt": reset,
            }
    if len(accounts) > 1:
        return 0, None
    return fetched * 1000, {"windows": list(slots.values())}


def select_snapshot(omarchy, export, now, account=None):
    fallback = payload(omarchy)
    fetched = omarchy.get("limitsFetchedAt")
    newer, candidate = opencode_snapshot(export, account)
    if candidate is None or (type(fetched) is int and newer <= fetched):
        return fallback
    active = [{i: w["resetAt"] for i, w in enumerate(s["windows"]) if w and w["resetAt"] > now}
              for s in (fallback, candidate)]
    old, new = active
    # A shared live reset is evidence of the same quota; never splice sources.
    if new and (not old or (old.keys() & new.keys()
                           and all(old[i] == new[i] for i in old.keys() & new.keys()))):
        return candidate
    return fallback


def read_record(source):
    try:
        record = json.loads(source.read_text())
        return record if isinstance(record, dict) else {}
    except (OSError, ValueError):
        return {}


def main():
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    result = select_snapshot(
        read_record(state / "omarchy/agents/usage/codex.json"),
        read_record(cache / "opencode/quota-export.json"),
        time.time(), os.environ.get("OPENCODE_QUOTA_ACCOUNT") or None,
    )
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
