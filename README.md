# AWTRIX NG Scripts

A collection of custom **Berry scripts** for [AWTRIX NG](https://ang.blueforcer.de/) — the next-generation firmware for ESP32-based LED matrix clocks.

These scripts run directly on the device, join the app rotation, and keep working even when nothing else on your network is online.

---

## Scripts

| Script | Description | Version |
|--------|-------------|---------|
| **[Anothertime](#anothertime)** | Always-on time display with rotating widgets (date, temperature, humidity, battery) and a week indicator | 1.1 |

More scripts will be added over time.

---

## Anothertime

A refined clock face that keeps the time visible at all times while cycling through additional information on the side.

### Features

- **Large time display** with smooth digit transitions (scroll or fade)
- **Seconds progress bar** along the bottom of the time
- **Rotating widgets**: date, temperature, humidity, battery (with custom icons)
- **Week indicator** with multiple visual styles
- Configurable colors, animation styles and durations
- Optional MQTT topic for external battery level

### Configuration options

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `sc` | color | Seconds bar color | `#FF00FF` |
| `ta` | select | Time animation (`scroll` / `fade`) | `fade` |
| `tad` | slider | Time animation duration (ms) | `500` |
| `wsty` | select | Week style (`large` / `progress` / `dotted` / `dotted2`) | `dotted2` |
| `wc` | color | Week days color | `#00FFFF` |
| `wdc` | color | Current day color | `#FF00FF` |
| `ssun` | bool | Week starts on Sunday | `false` |
| `wa` | select | Widgets animation (`scroll` / `fade`) | `fade` |
| `wad` | slider | Widgets animation duration (ms) | `500` |
| `btopic` | text | MQTT topic for battery level (leave empty to use sensor) | `""` |
| `wdur` | slider | Default widget duration (s) | `2` |
| `wlist` | text | Widgets list (e.g. `date,temperature@5,humidity,battery`) | `date,temperature,humidity,battery` |

You can override the duration of individual widgets in `wlist` with the `@N` suffix (e.g. `temperature@5`).

### Installation

1. Open the AWTRIX NG web UI → **Scripts** tab
2. Create a new script named `Anothertime`
3. Paste the content of [`anothertime.ax`](anothertime.ax)
4. Save — the script appears in the app rotation

Alternatively, upload via the HTTP API:
it 
```bash
curl -H "Content-Type: text/plain" \
     -X PUT \
     --data-binary @anothertime.ax \
     http://<awtrix-ip>/api/v1/apps/script/Anothertime