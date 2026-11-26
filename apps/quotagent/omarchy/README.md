# Publish Codex quotas from Omarchy and OpenCode Quota

This optional relay reads Omarchy’s existing `codex.json` cache in its user state directory (`~/.local/state/omarchy/agents/usage/` by default). It publishes the account-wide 5-hour and weekly quotas using the [Quotagent MQTT contract](../MQTT.md). It runs once on user-manager startup and again when the cache file changes; it does not start Codex or poll.

## Install the relay

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

## Optional: use fresher OpenCode Quota readings

Enable **Quota file (JSON)** in [OpenCode Quota](https://github.com/slkiser/opencode-quota/blob/main/docs/readme/external-integration.md), or merge `"system": { "exportFile": true }` into `~/.config/opencode/opencode-quota/settings.jsonc`. Leave `system.exportPath` at its default (`$XDG_CACHE_HOME/opencode/quota-export.json`, usually `~/.cache/opencode/quota-export.json`). The same watcher reacts to either file; the relay does not request additional quota checks.

The relay uses a valid OpenAI export if its provider `fetchedAt` is newer than Omarchy’s `limitsFetchedAt`. When both sources have active windows, at least one must overlap and all overlapping reset times must match. The relay publishes one snapshot, never a mix of the two. If the export is missing, older, expired, rejected, or ambiguous, Omarchy remains the fallback.

If OpenCode Quota exports multiple OpenAI logins, set `OPENCODE_QUOTA_ACCOUNT` in `mqtt.env` to the exact exported `account` label. If that still matches duplicate rows, the export is ignored. Keep Omarchy and OpenCode on the same account; matching reset times are a check, not proof of account identity.

Already installed? Recopy the script and both units as in step 3, run `systemctl --user daemon-reload`, then `systemctl --user restart quotagent-omarchy-relay.path quotagent-omarchy-relay.service`.
