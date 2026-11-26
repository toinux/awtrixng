import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("relay", Path(__file__).with_name("relay.py"))
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)


class PayloadTest(unittest.TestCase):
    def test_selects_newer_export_without_mixing_accounts_or_sources(self):
        omarchy = {"limitsFetchedAt": 100_500, "limits": [
            {"label": "5h window", "percent": 0.05, "resetsAt": "1970-01-01T01:00:00Z"},
            {"label": "Weekly (7-day)", "percent": 0.91, "resetsAt": "1970-01-02T00:00:00Z"},
        ]}
        row = {"id": "openai.five_hour", "account": "Personal", "renderType": "percent",
               "percentRemaining": 93, "resetAt": 3600}
        provider = {"status": "ok", "fetchedAt": 101, "entries": [row]}
        export = {"version": 3, "providers": {"openai": provider}}

        def remaining(account=None):
            windows = relay.select_snapshot(omarchy, export, 101, account)["windows"]
            return [w["remainingPercent"] if w else None for w in windows]

        self.assertEqual(remaining(), [93, None])
        provider["fetchedAt"] = 100
        self.assertEqual(remaining(), [95, 9])
        provider["fetchedAt"] = 101
        provider["status"] = "error"
        self.assertEqual(remaining(), [95, 9])
        provider["status"] = "ok"
        row["resetAt"] = 3700
        self.assertEqual(remaining(), [95, 9])
        row["resetAt"] = 3600
        provider["entries"].append(dict(row, account="Work", percentRemaining=60))
        self.assertEqual(remaining(), [95, 9])
        self.assertEqual(remaining("Personal"), [93, None])
        self.assertEqual(remaining("Work"), [60, None])
        self.assertEqual(relay.select_snapshot({}, export, 3600, "Personal")["windows"], [None, None])

    def test_order_fraction_and_invalid_slot(self):
        result = relay.payload({"limits": [
            {"label": "Weekly (7-day)", "percent": 0.25123456789, "resetsAt": "2030-01-01T00:00:00Z"},
            {"label": "Weekly (7-day)", "title": "Separate model", "percent": 0.99, "resetsAt": "2030-01-01T00:00:00Z"},
            {"label": "5h window", "percent": 0.72, "resetsAt": "bad"},
        ]})
        self.assertEqual([window["durationSeconds"] if window else None for window in result["windows"]],
                         [None, 604800])
        self.assertIsNone(result["windows"][0])
        self.assertEqual(result["windows"][1]["remainingPercent"], 74.876543211)
        self.assertEqual(relay.payload({})["windows"], [None, None])

    def test_publish_retained_without_credentials_in_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "omarchy/agents/usage/codex.json"
            cache.parent.mkdir(parents=True)
            cache.write_text(json.dumps({"limits": []}))
            env = {"XDG_STATE_HOME": directory, "XDG_CACHE_HOME": directory, "MQTT_HOST": "broker",
                   "MQTT_PORT": "1884", "MQTT_TOPIC": "custom/topic"}
            with patch.dict(os.environ, env, clear=True), patch.object(relay.subprocess, "run") as run:
                relay.main()
            args, kwargs = run.call_args
            self.assertEqual(args[0], ["mosquitto_pub", "-h", "broker", "-p", "1884",
                                       "-t", "custom/topic", "-q", "1", "-r", "-s"])
            self.assertTrue(kwargs["check"])
            self.assertEqual(json.loads(kwargs["input"]), {"windows": [None, None]})

    def test_publish_failure_does_not_log_argv_or_password(self):
        secret = "not-for-logs"
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "omarchy/agents/usage/codex.json"
            cache.parent.mkdir(parents=True)
            cache.write_text('{"limits":[]}')
            with patch.dict(os.environ, {"XDG_STATE_HOME": directory, "XDG_CACHE_HOME": directory}, clear=True), \
                 patch.object(relay.subprocess, "run", side_effect=subprocess.CalledProcessError(
                     1, ["mosquitto_pub", "-P", secret])), \
                 contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(relay.entrypoint(), 1)
        self.assertNotIn(secret, stderr.getvalue())
        self.assertNotIn("mosquitto_pub", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
