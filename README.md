# AWTRIX NG Scripts

A collection of custom **Berry scripts** for [AWTRIX NG](https://ang.blueforcer.de/) — the next-generation firmware for ESP32-based LED matrix clocks.

These scripts run directly on the device and join the app rotation. Clock and onboard-sensor displays work locally; MQTT values require a configured broker and a publishing source to refresh.

---

## Scripts

| Script | Description | Version |
|--------|-------------|---------|
| **[Anothertime](#anothertime)** | Always-on time display with rotating widgets (date, temperature, humidity, battery) and a week indicator | 1.4.0 |
| **[Tesla](#tesla)** | TeslaMate battery level, charging power and animated plug | 1.6.0 |
| **[Quotagent](#quotagent)** | One or two usage quotas with countdowns and pace markers over MQTT | 1.0.0 |

---

## Anothertime

A refined clock face that keeps the time visible at all times while cycling through additional information on the side.

See the [Anothertime project notes](apps/anothertime/ANOTHERTIME.md) for its detailed history and behavior.

### Features

- **Time display** with smooth digit transitions (scroll or fade)
- **Seconds progress bar** along the bottom of the time: it fills up over the minute, then plays an end-of-minute animation during the last 500 ms — `rewind` (the bar drains back to empty), `fade` (the full bar dims out) or `none` (no animation, it just restarts)
- **Rotating widgets**: date, temperature, humidity, battery (with hand-drawn icons; no icon assets required)
- **Date styles**: classic icon or calendar block
- **Week indicator** with multiple visual styles (`large`, `progress`, `dotted`, `dotted2`)
- Uses **system colors** (time, date, temperature, humidity, battery, calendar header/body/text) so the face follows your AWTRIX theme
- Temperature respects the device **Celsius / Fahrenheit** setting
- Configurable animation styles and durations
- Optional MQTT topics for temperature, humidity and battery; MQTT temperature must be in Celsius and follows the device's Fahrenheit preference. Temperature and humidity are rounded like onboard readings. A configured topic replaces its onboard sensor; unavailable values display `?`.
- Values longer than 2 digits scroll with a bounce animation

### Configuration options

| Setting | Type | Description | Default |
|---------|------|-------------|---------|
| `sc` | color | Seconds bar color | `#FF00FF` |
| `sa` | select | Seconds animation (`none` / `rewind` / `fade`) | `rewind` |
| `ta` | select | Time animation (`scroll` / `fade`) | `fade` |
| `tad` | slider | Time animation duration (ms) | `500` |
| `dsty` | select | Date style (`icon` / `calendar`) | `icon` |
| `wsty` | select | Week style (`large` / `progress` / `dotted` / `dotted2`) | `dotted2` |
| `wc` | color | Week days color | `#00FFFF` |
| `wdc` | color | Current day color | `#FF00FF` |
| `ssun` | bool | Week starts on Sunday | `false` |
| `wa` | select | Widgets animation (`scroll` / `fade`) | `fade` |
| `wad` | slider | Widgets animation duration (ms) | `500` |
| `ttopic` | text | MQTT topic for temperature (leave empty to use the onboard sensor) | `""` |
| `htopic` | text | MQTT topic for humidity (leave empty to use the onboard sensor) | `""` |
| `btopic` | text | MQTT topic for battery level (leave empty to use the onboard sensor) | `""` |
| `wlist` | text | Widgets list (e.g. `date,temperature@5,humidity,battery`) | `date,temperature,humidity,battery` |

Default widget duration is **3 seconds**. You can override the duration of individual widgets in `wlist` with the `@N` suffix (1–60 seconds, e.g. `temperature@5`). An empty or entirely invalid list falls back to the date widget; entries must use the listed names without surrounding spaces.

### Installation

1. Open the AWTRIX NG web UI → **Scripts** tab  
2. Create a new script named `Anothertime`  
3. Paste the content of [`anothertime.ax`](apps/anothertime/src/anothertime.ax)
4. Save — the script appears in the app rotation  

Alternatively, upload via the HTTP API:

```bash
curl -H "Content-Type: text/plain" \
     -X PUT \
     --data-binary @anothertime.ax \
     http://<awtrix-ip>/api/v1/apps/script/Anothertime
```

AWTRIX NG v1.1.1+ has no fixed script size limit: an install needs enough contiguous free memory for the source plus compile headroom. Prefer minified deployment (below); a `507` reply means memory is insufficient or fragmented.

---

## Tesla

[`tesla.ax`](apps/tesla/src/tesla.ax) displays TeslaMate data received through the MQTT broker configured on AWTRIX NG.

- **Battery percentage**, including `100%`; `--` until a valid value arrives.
- **Charging power** alternates with the percentage while TeslaMate reports `Charging`. Each view lasts **3 seconds** by default (`page` setting); the app stays for both views.
- **Plug icon**: green when connected, red when disconnected, with an animated electrical flow during charging.
- **Bottom bar**: battery level in green (cyan while charging), charge-limit remainder in purple, unused remainder in the background color. Battery fill takes precedence when it exceeds the limit.
- Temperatures are omitted because they can remain unavailable or outdated while the vehicle sleeps. Battery values are the last values reported by TeslaMate, not a live reading of a sleeping car.

Set **Car** (`id`) to the TeslaMate car ID and **Namespace** (`ns`) if used. Colors, flow speed, trail length and view duration are configurable through the app settings. A missing, invalid or negative power value leaves the percentage displayed; power is never displayed outside active charging.

Install with `./deploy.sh tesla`, or paste the complete source into a script named `Tesla` in the web UI. Deployment requires `AWTRIX_IP` and optional `AWTRIX_AUTH` in `.env`. The script creates only by default; use `./deploy.sh tesla --force` to replace an installed app without remote-change protection.

---

## Quotagent

[`quotagent.ax`](apps/quotagent/src/quotagent.ax) shows one quota across the panel or two side by side. The white two-pixel tick shows how much quota would remain at an even pace. The three bar colors are configurable: **On pace** (green), **Behind pace** (orange, more than five percentage points below pace), and **Low quota** (red). Low quota takes priority below **Low quota threshold (%)** (default `20`; `0` disables it).

Install with `./deploy.sh quotagent`, then configure **MQTT topic** on the app to match your publisher. By default it joins the regular rotation. Enable **Show on change** to skip regular turns and show a five-second notification when a known percentage changes, without switching the active app. The first reading, a layout change, and a reset timestamp change alone do not trigger a notification.

- [MQTT publisher contract](apps/quotagent/MQTT.md): exact format, invalid data rules and a test publisher.
- [Omarchy setup](apps/quotagent/omarchy/README.md): optional Codex relay, no polling.
- [Pixel simulator](apps/quotagent/simulator.html): open locally without a panel.

---

## Development

Each application is an `awtrix-cli` project under `apps/`, with its own `awtrix.toml` and `src/` directory. Validate a project locally with `awtrix-cli project validate --manifest apps/anothertime/awtrix.toml` or `apps/tesla/awtrix.toml`. Minification and deployment use the installed `awtrix-cli`; its release workflow pin is updated periodically. Python display/MQTT tools use Python 3's standard library.

For deployment, copy `.env.example` to `.env`, set `AWTRIX_IP`, and set optional `AWTRIX_AUTH=user:pass` when device authentication is enabled. `deploy.sh` loads this file; Python tools also accept environment overrides. Deployment creates an app only if it is absent; `--force` explicitly enables unconditional replacement. Local `.env` and generated `*.min.ax` files are ignored by Git.

```bash
# minify: creates apps/anothertime/src/anothertime.min.ax beside the source
awtrix-cli minify apps/anothertime/src/anothertime.ax

# create an app on the configured device (create-only)
./deploy.sh anothertime

# replace an already-installed app (unconditional)
./deploy.sh tesla --force
```

Successful minification does not verify Berry syntax. A script that fails to compile still installs — require `"error": null` in the upload reply, then capture the running app to check its display. The minifier's field-renaming constraints are documented in [`AGENTS.md`](AGENTS.md#minifier-constraints).

### Agent setup

Run from the repo root with Python 3 on Linux or macOS:

```sh
python3 tools/berry-skill.py check    # compare with the current official ZIP, without writing
python3 tools/berry-skill.py install  # install on a fresh clone or update in place
```

This installs a project-local adaptation of [Blueforcer’s official Berry skill](https://blueforcer.github.io/awtrix-ng/esp32/guides/ai-prompt/#as-an-agent-skill) at `.agents/skills/awtrix-berry-app/`. Start a fresh agent session if your current one already loaded the skill. The generated `SKILL.md` sends the agent to the relevant API topics; `awtrix-cli` still handles supported device operations. Firmware notes in [`AGENTS.md`](AGENTS.md#script-conventions-awtrix-specific) take precedence over older upstream size limits.

- **Check:** exit `0` means current, `1` means missing or different, `2` means the ZIP could not be fetched or processed. Nothing runs automatically during a Berry task.
- **Update:** `install` replaces the local skill directory when generated files differ. Save any hand edits you want to keep first. The tool validates and stages the replacement before moving the current copy; a structure error leaves your current copy in place.
- **Offline or repeatable install:** append `--archive /path/to/official.zip` to either command. The installed `UPSTREAM.md` records Blueforcer’s notice, the license and the ZIP SHA-256, which identifies the exact input even if the download is replaced upstream.

The [installer and heading rules](tools/berry-skill.py) and the [entry template](tools/berry-skill.md) are versioned. The generated skill is ignored by Git and intended for local use under its upstream license. If upstream changes the layout, review the official ZIP, adjust the rules and index together, and run `python3 -m unittest discover -s tools -p 'test_berry_skill.py'`.

### Releases

Releases are per application, using tags `<script>-vMAJOR.MINOR.PATCH` with an optional prerelease suffix, such as `tesla-v1.6.0-rc.1`. The workflow verifies the tag version against the source `# @version` (the prerelease suffix is not part of that source version), then uses pinned `awtrix-cli` v0.3.1 to create the minified `<script>-<version>.ax` asset. Keep the source header, table and stable tag version aligned. Review the CLI pin periodically as it evolves. Release prerequisites and permission checks are in [`AGENTS.md`](AGENTS.md#commands).

### Tesla display checks

```bash
# Read retained battery / charging values from AWTRIX's MQTT broker
python3 tools/mqtt-read.py --car-id 2

# Capture the actual display after pinning Tesla
python3 tools/awtrix-screen.py --app Tesla --wait 0.3 --out /tmp/opencode/tesla.png

# Test eleven simulated states on the physical display; save PNGs and raw frames
python3 tools/tesla-mockups.py
```

The mockup tool temporarily installs `TeslaMock` using the actual renderer, copies the production configuration as diagnostic defaults, and disables its production MQTT subscriptions. It sends non-retained test data on a unique `awtrixng/mock/tesla/...` topic. It checks compilation/runtime errors, the battery/limit bar and automatic battery-to-power alternation, then deletes the diagnostic app and restores the previously active app.

Images and framebuffer JSON are saved under `/tmp/opencode/tesla-mockups`; `all.png` is a vertical contact sheet in the printed scenario order. Use `--out-dir` for another location or repeat `--case` to select scenarios (see `--help`). This tool changes the physical display and requires deployment permission. Inspect the images to verify glyphs and spacing, in addition to the automated checks.
