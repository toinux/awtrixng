# AWTRIX NG Berry apps

Use the references below for documented AWTRIX NG Berry bindings. These
references contain upstream examples and workflow advice; follow the project
`AGENTS.md` and this workflow for device operations and delivery.

1. For `.ax` edits, read [app structure and lifecycle](references/app-structure.md).
   Check the [hardware matrix](references/hardware.md) when panel size or
   hardware features matter. Use `width()` and `height()` rather than assuming
   a panel size. Read only the other references that match the change.
2. Put user-adjustable values in `# @config` headers and read them with
   `store.get(key)` without repeating the default. Never put real credentials
   in a script. Keep allocations out of `draw()` and respect the shared Berry heap.
3. Follow the `awtrix-cli` skill for operations it covers, including minifying,
   inspecting, deploying, and verifying. Get permission before changing the
   physical device. Report compilation and runtime results separately from
   minification. Verify headless scripts by their effects instead of the panel.
4. Leave the complete `.ax` file on disk when the user can access it. Report its
   path and checks. Provide the full source once if asked or if no file can be
   shared. For manual web UI installation, read the handoff reference below.

## Choose references by task

- Import requirements and available globals → [API basics](references/api-basics.md)
- Drawing primitives, fonts, charts, effects, icons → [drawing](references/drawing.md)
- Panel composition and legibility → [panel design](references/panel-design.md)
- Clock, timers, buttons → [time and input](references/time-and-input.md)
- HTTP, Modbus, MQTT, regex, notifications → [networking](references/networking.md)
- `@config`, store and shared values → [state and shared settings](references/state-and-modules.md)
- Sensors, rotation, display power, logging, math and device settings → [device features](references/device-features.md)
- Playback, recording or music → [audio](references/audio.md)
- Headless scripts and reusable imports → [script modes and modules](references/script-modes.md)
- Berry syntax, unsupported features, heap or firmware limits → [language and memory](references/language-and-memory.md)
- Full network-backed app pattern → [worked example](references/example.md)
- Pre-delivery review or troubleshooting → [checklist](references/checklist.md)
- Web UI install or user-facing error follow-up → [handoff](references/handoff.md)
- Gamepad, BLE, crypto, OAuth, TCP → [advanced APIs](references/advanced.md)
- API keys and `@secret` → [secrets](references/secrets.md)
- Speech recognition and synthesis → [voice](references/voice.md)
- Original prompt and response conventions, for upstream comparison → [upstream workflow](references/upstream-workflow.md)

[Upstream attribution, license and ZIP revision](UPSTREAM.md).
