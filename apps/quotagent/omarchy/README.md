# Publish Codex quotas from Omarchy

This optional relay reads Omarchy’s existing `codex.json` cache in its user state directory (`~/.local/state/omarchy/agents/usage/` by default). It publishes the account-wide 5-hour and weekly quotas using the [Quotagent MQTT contract](../MQTT.md). It runs once on user-manager startup and again when the cache file changes; it does not start Codex or poll.

1. Set up Codex in Omarchy’s Agents widget and check that `codex.json` exists. Install the `mosquitto` package for `mosquitto_pub` (`omarchy pkg add mosquitto`). The relay also needs Python 3; it does not run a broker.
2. If the AWTRIX broker is not `localhost:1883`, set its host and port in `~/.config/quotagent/mqtt.env` (under `$XDG_CONFIG_HOME` if set). Set `MQTT_TOPIC` only to override the default `quotagent/status`.

   ```ini
   MQTT_HOST=your-broker.example
   MQTT_PORT=1883
   ```

   If the broker requires authentication, put `-u username` and `-P password` on separate lines in the native `mosquitto_pub` config (`~/.config/mosquitto_pub` by default) and restrict the file to mode `600`. Do not put secrets in the MQTT payload.

3. From the repository root, install and start the relay:

   ```sh
   config="${XDG_CONFIG_HOME:-$HOME/.config}"
   relay=apps/quotagent/omarchy
   install -Dm644 "$relay/relay.py" "$HOME/.local/lib/quotagent/relay.py"
   mkdir -p "$config/systemd/user"
   install -m644 "$relay/quotagent-omarchy-relay.path" "$relay/quotagent-omarchy-relay.service" "$config/systemd/user/"
   systemctl --user daemon-reload
   systemctl --user enable --now quotagent-omarchy-relay.path quotagent-omarchy-relay.service
   ```

The watcher should be `active (waiting)`; the publisher is a one-shot service and is normally inactive between runs. After changing MQTT settings, run `systemctl --user start quotagent-omarchy-relay.service` to republish. If it fails, check `journalctl --user -u quotagent-omarchy-relay.service -n 20`.
