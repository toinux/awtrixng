# Anothertime

## Changes
* 1.0.0 : first release
* 1.1.0 : battery widget, customization of widget orders and duration, other fixes...
* 1.2.0 : add calendar style for date, use more system colors
* 1.3.0 : seconds rewind effect
* 1.4.0 : configurable seconds bar animation (none / rewind / fade), MQTT topics for temperature, humidity and battery

## Description
**An always-on clock that packs time, seconds, weekday and a rotating widget onto a single 32×8 panel.**

Anothertime is a compact "everything at once" clock face: a big HH:MM readout with animated digit
transitions, a seconds-progress bar, a weekday indicator, and a small rotating widget (date /
temperature / humidity / battery) in the corner — all on the same screen, all the time.

The end-of-minute seconds animation lasts 500 ms. Widget dwell time defaults to 3 seconds and
can be overridden per entry in the widget list.

Use minified source for deployment to reduce installation memory pressure. Source and
installation instructions: https://github.com/toinux/awtrixng#anothertime

## Requirements

- **AWTRIX NG.** No PSRAM or extra memory needed — the script draws everything with primitives, no icons.
- **Time sync (NTP) strongly recommended.** The clock, the seconds bar and the weekday indicator
  all read the device's wall clock; before it syncs they simply won't show meaningful values.
- **Temperature / humidity sensor: optional.** If your board has none (or you'd rather not use it),
  those two widgets just show `?` instead of a reading — nothing breaks. Both can also come from an
   **MQTT topic** instead of the onboard sensor. MQTT temperature readings are in Celsius;
   configured topics replace the sensor without falling back to it when data is missing.
- **No network requests, no API keys, no icons required.** Everything is drawn on-device (MQTT is
  optional and only used if you configure a topic).

## What you see on screen

- **Time (top-left):** `HH:MM`. The colon pulses during odd-numbered seconds and is off during
  even-numbered seconds. When the minute changes, each changed digit animates from old to new — either
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

The [configuration table in the README](../../README.md#configuration-options) is the maintained
settings reference. The `@N` widget-list suffix sets a dwell time in seconds (1–60).
