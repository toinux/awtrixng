# Anothertime

## Changes
* 1.0 : first release
* 1.1 : battery widget, customization of widget orders and duration, other fixes...
* 1.2 : add calendar style for date, use more system colors
* 1.3 : seconds rewind effect
* 1.4 : configurable seconds bar animation (none / rewind / fade), MQTT topics for temperature and humidity

## Description
**An always-on clock that packs time, seconds, weekday and a rotating widget onto a single 32×8 panel.**

Anothertime is a compact "everything at once" clock face: a big HH:MM readout with animated digit
transitions, a seconds-progress bar, a weekday indicator, and a small rotating widget (date /
temperature / humidity / battery) in the corner — all on the same screen, all the time.

> This app is still evolving — the only thing still hardcoded is the length of the end-of-minute
> seconds animation (500 ms). Everything else below is a setting. It's fully usable as-is.

The script is minified to about 7.3 KB before deployment (the old 8192-byte script limit is gone
as of AWTRIX NG v1.1.1, but a smaller script leaves more heap free for the rest of the firmware),
the original source code is available at https://github.com/toinux/awtrixng

## Requirements

- **AWTRIX NG.** No PSRAM or extra memory needed — the script draws everything with primitives, no icons.
- **Time sync (NTP) strongly recommended.** The clock, the seconds bar and the weekday indicator
  all read the device's wall clock; before it syncs they simply won't show meaningful values.
- **Temperature / humidity sensor: optional.** If your board has none (or you'd rather not use it),
  those two widgets just show `?` instead of a reading — nothing breaks. Both can also come from an
  **MQTT topic** instead of the onboard sensor.
- **No network requests, no API keys, no icons required.** Everything is drawn on-device (MQTT is
  optional and only used if you configure a topic).

## What you see on screen

- **Time (top-left, large digits):** `HH:MM`. The colon between hours and minutes fades in and out
  once a second. When the minute changes, the two affected digits animate from old to new — either
  a **fade** cross-dissolve or a **scroll** (digits slide past each other), your choice.
- **Seconds bar (bottom-left, columns 0–16):** fills left to right over the course of each minute,
  with a softly-fading pixel at the leading edge instead of a hard cutoff. Over the last 500 ms of
  every minute an end-of-minute animation plays, selectable in the settings: **rewind** (the bar
  drains back to empty), **fade** (the full bar dims out), or **none** (the bar simply restarts).
- **Weekday indicator (bottom-right, columns 18–31):** a small row of dots/segments showing where
  in the week you are, in one of four visual styles, with today highlighted in its own color.
  The week can start on Sunday or Monday.
- **Rotating widget (top-right corner):** cycles automatically between:
  - **Date** — day of the month, with a little calendar icon (or a compact calendar block, your choice)
  - **Temperature** — from the device's sensor or an MQTT topic, rounded, with a thermometer icon
    (follows the device's Celsius / Fahrenheit setting)
  - **Humidity** — from the device's sensor or an MQTT topic, rounded, with a droplet icon
  - **Battery** — from the device or from a MQTT topic, with dynamic battery icon

  Which widgets appear, in which order and how long each one dwells are all configurable. Each
  switch animates smoothly between the outgoing and incoming widget (icon and value together) —
  either a cross-fade or a vertical scroll, your choice.
- The **time, date, temperature, humidity, battery and calendar colors** automatically follow your
  device's system colors of the same name (falling back to **Default text color** where a system
  color is unset) — including live changes, no restart needed. The seconds bar and the weekday
  indicator have their own color settings.

## Settings

Go to the **Apps** tab → the **⋯** menu on Anothertime's row → **Settings**. Saving restarts the app.

| Setting | What it does | Default |
|---------|--------------|---------|
| **Seconds color** (`sc`) | Color of the seconds bar | `#FF00FF` |
| **Seconds animation** (`sa`) | End-of-minute animation: `none`, `rewind` or `fade` | `rewind` |
| **Time animation** (`ta`) | How the digits change at the minute turn: `scroll` or `fade` | `fade` |
| **Time animation duration** (`tad`) | Length of the digit animation | `500 ms` |
| **Date style** (`dsty`) | `icon` (calendar page) or `calendar` (block) | `icon` |
| **Week style** (`wsty`) | `large`, `progress`, `dotted` or `dotted2` | `dotted2` |
| **Week days color** (`wc`) | Color of the unhighlighted days in the week row | `#00FFFF` |
| **Current day color** (`wdc`) | Color of today in the week row | `#FF00FF` |
| **Week starts Sunday** (`ssun`) | Start the week on Sunday instead of Monday | `false` |
| **Widgets animation** (`wa`) | How widgets swap: `scroll` or `fade` | `fade` |
| **Widgets animation duration** (`wad`) | Length of the widget swap animation | `500 ms` |
| **Temperature topic** (`ttopic`) | MQTT topic for temperature (empty = onboard sensor) | *(empty)* |
| **Humidity topic** (`htopic`) | MQTT topic for humidity (empty = onboard sensor) | *(empty)* |
| **Battery topic** (`btopic`) | MQTT topic for the battery level (empty = system value) | *(empty)* |
| **Widgets** (`wlist`) | Widget list and per-widget dwell time, e.g. `date,temperature@5,humidity,battery` | `date,temperature,humidity,battery` |

Widget dwell times are in seconds and default to **3 seconds**; the `@N` suffix overrides the
duration for a single widget (1–60).
