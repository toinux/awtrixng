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
            env = {"XDG_STATE_HOME": directory, "MQTT_HOST": "broker",
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
            with patch.dict(os.environ, {"XDG_STATE_HOME": directory}, clear=True), \
                 patch.object(relay.subprocess, "run", side_effect=subprocess.CalledProcessError(
                     1, ["mosquitto_pub", "-P", secret])), \
                 contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(relay.entrypoint(), 1)
        self.assertNotIn(secret, stderr.getvalue())
        self.assertNotIn("mosquitto_pub", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
