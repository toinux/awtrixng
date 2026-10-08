# Tesla MQTT troubleshooting

Use this note for missing TeslaMate values, subscription changes or physical display mockups.

## Historical battery subscription incident

The Tesla app's configured car ID and namespace determine its TeslaMate topics. With ID `2` and an empty namespace, the broker topics are under `teslamate/cars/2/`.

For the battery display incident, the broker had retained `battery_level = 80`. The other retained values were `charge_limit_soc = 80`, `charging_state = Complete`, `inside_temp = 18.6`, and `outside_temp = 16.0`. AWTRIX received callbacks for the temperatures, charge limit, and charging state, but the exact `battery_level` subscription did not update SOC. A wildcard subscription delivered the battery value and made `80` appear on the display.

`apps/tesla/src/tesla.ax` listens for `teslamate/cars/+/battery_level` (or `teslamate/<namespace>/cars/+/battery_level` when configured) and applies the payload only when its topic matches the configured car ID. This is a verified workaround; the reason the exact subscription failed on the device has not been established.

## Follow-up device tests (2026-10-04)

The earlier exact-filter failure could not be reproduced on the device running AWTRIX NG 1.1.2. Temporary diagnostic apps were removed after testing.

- An app subscribing only to `teslamate/cars/2/battery_level` displayed the retained `80` (`R1 80`). After one non-retained publication of `80` on that topic, it displayed a second callback (`R2 80`).
- The same exact subscription still received retained and fresh messages when registered alongside the four other TeslaMate filters used by Tesla.
- A second temporary app holding the same exact filter did not prevent either callback from reaching the probe app.
- A diagnostic copy of the Tesla app's full logic, changed only to subscribe to the exact car-2 battery topic, compiled without error and displayed the retained SOC `80`.
- The filters `teslamate/cars/2/+` and `teslamate/cars/2/#` also delivered the battery value.

These results show that the exact filter, retained replay, fresh-message routing, tested sibling subscriptions and cross-app duplicate-subscription fan-out all work on firmware 1.1.2. They do **not** explain the earlier failure: it remains unreproduced, and no firmware fix or specific cause is established. The production Tesla app was not replaced during these tests, so its wildcard workaround remains in place pending a reproducible regression against the production app or a relevant firmware version.

## Read broker values

Run the project tool to read retained TeslaMate values. It obtains broker connection settings from AWTRIX's `/api/v1/system` endpoint, using `AWTRIX_IP` and optional `AWTRIX_AUTH` from the environment or `.env`:

```sh
python3 tools/mqtt-read.py --car-id 2 --namespace home
python3 tools/mqtt-read.py --topic teslamate/cars/2/battery_level
```

The output includes each payload and whether the broker marked it retained. The tool uses Python's standard library and does not require a separate MQTT package.

## Verify the AWTRIX display

After an authorized deployment, pin the Tesla app and capture the framebuffer using the [display-check commands](../../README.md#tesla-display-checks).

Completion requires `/api/v1/device` to report `currentApp: Tesla`, the Tesla entry in `/api/v1/apps` to have `error: null`, and the framebuffer to match the current broker values and saved config. For the historical battery incident, the expected value was `80`; it is not a current test fixture.

Deployments change the physical display. Follow the deploy approval rule in `AGENTS.md` before installing a diagnostic or production script.

## Battery / power display (Tesla 1.6.0)

The app no longer subscribes to `inside_temp` or `outside_temp`. It displays battery percentage and, only while `charging_state = Charging`, alternates with `charger_power` in kW. Invalid or negative power suppresses the power page; a valid zero remains `0kW`. `page` controls seconds per view and `duration()` reserves two views during charging. The existing wildcard battery workaround, plug animation and layered SOC/limit bar remain.

## Mockups

Run the [mockup tool](../../README.md#tesla-display-checks) after authorized renderer changes. Its `CASES` list is the scenario source of truth; `--help` lists selection options. Completion requires all selected cases to pass and visual inspection of the contact sheet. Run the full suite to exercise automatic alternation as well as static views.

Two device-specific constraints explain the tool's structure:

- **Compile once:** reinstalling once per scenario caused `507` after ten cases. One temporary app receives successive simulated states over an isolated MQTT topic.
- **Same dwell:** re-pinning resets the page timer in `on_show()`. The timed alternation check stays within one dwell and confirms the app is active before reading the second frame. Independent captures pin immediately before reading.

Verification on 2026-10-04 passed all scenarios and the battery-to-power transition. Production Tesla 1.6 compiled with `error: null`; the framebuffer matched retained SOC `74`, limit `80` and charging state `Stopped`. `TeslaMock` was removed after testing.
