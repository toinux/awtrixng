# Quotagent MQTT publisher contract

Publish one complete UTF-8 JSON snapshot to `quotagent/status` on the broker configured in AWTRIX. If you use a different topic, set **MQTT topic** in Quotagent to match. Publish with **retain enabled** so the app receives the last snapshot after restart; QoS 1 is recommended. Do not split the windows across messages.

```json
{
  "windows": [
    {"durationSeconds": 18000, "remainingPercent": 28, "resetAt": 1893456000},
    {"durationSeconds": 604800, "remainingPercent": 38, "resetAt": 1893542400}
  ]
}
```

| Field | Publisher requirement |
|---|---|
| `windows` | Array: one entry for full width; two entries for left and right, in that order. Use `[]` to mark everything unavailable. |
| `durationSeconds` | Positive JSON number: total length of the window in seconds, not time remaining. |
| `remainingPercent` | JSON number from `0` through `100`, including decimals. If the source reports **used** percent, subtract it from 100. |
| `resetAt` | Positive Unix timestamp in whole **seconds**, not milliseconds, an ISO string, or a relative delay. |

For two windows, publish `null` in an unavailable slot to preserve the layout: `{"windows":[null,{"durationSeconds":604800,"remainingPercent":38,"resetAt":1893542400}]}`. Missing fields, invalid numbers, or a reset at or before the panel clock show `---` for that slot. An absent or malformed snapshot, or more than two entries, shows one centered `---`. Expiration does not assume the quota refilled or move the other window. There is no expiration timer other than `resetAt`.

Keep a stable order. In optional **Show on change** mode, the first snapshot, a new layout or window duration, and changes to `resetAt` alone do not trigger a notification. A changed percentage for a known window does, even if it does not change the number of lit LEDs. The notification lasts five seconds and does not switch the active app.

## Test publisher

Replace `YOUR_BROKER` with your broker. This sends a fresh example with 1 h 54 min and 1.5 days until reset:

```sh
now=$(date +%s)
printf '{"windows":[{"durationSeconds":18000,"remainingPercent":28,"resetAt":%s},{"durationSeconds":604800,"remainingPercent":38,"resetAt":%s}]}' \
  "$((now + 6840))" "$((now + 129600))" |
  mosquitto_pub -h YOUR_BROKER -t quotagent/status -q 1 -r -s
```

This replaces the retained snapshot on that topic. Use a separate topic and match the app setting if a live publisher is already running.
