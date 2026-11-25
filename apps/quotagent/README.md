See how much AI quota you have left, when it resets, and whether you’re using it faster than planned. Quotagent shows one quota full-width or two side by side on a 32 × 8 AWTRIX NG display. The white tick marks how much quota would remain at an even pace. Bar colors and the low-quota threshold are adjustable.

Use it with **OpenAI Codex**, **Anthropic Claude / Claude Code**, **Google Antigravity**, **Kimi Code**, **MiniMax**, **Z.ai**, **Alibaba Coding Plan**, or any source that exposes compatible quota data. **A separate MQTT publisher is required.** Quotagent does not sign in to providers or fetch quotas itself.

## Setup

1. Install Quotagent and enable MQTT on your AWTRIX NG.
2. Publish a single retained JSON message to `quotagent/status` on the **same MQTT broker**. If you use a different topic, set **MQTT topic** in Quotagent to match.
3. Keep Quotagent in your regular rotation, or enable **Show on change** for a five-second notification that leaves the current app in place.

**Codex on Omarchy?** Use the [ready-made Omarchy relay](https://github.com/toinux/awtrixng/blob/main/apps/quotagent/omarchy/README.md). For other setups, see the [MQTT contract and test command](https://github.com/toinux/awtrixng/blob/main/apps/quotagent/MQTT.md).

## Copy this prompt into your coding agent

> Set up an MQTT quota publisher for Quotagent on my AWTRIX NG for [provider and plan]. Read the [Quotagent MQTT contract](https://github.com/toinux/awtrixng/blob/main/apps/quotagent/MQTT.md). Find a quota source I already have access to; for Codex on Omarchy, use the existing cache and relay. Ask me for any missing details, including the broker host and port and which quota windows to show.
>
> Publish a single retained JSON object with a `windows` array of one or two entries to `quotagent/status` on the broker used by AWTRIX. Each entry needs `durationSeconds` (the full window length), `remainingPercent` (0–100, not used percent), and `resetAt` (Unix seconds, not milliseconds). Keep the order stable. Set up automatic updates using the source’s existing refresh mechanism if possible.
>
> Verify that a new MQTT subscriber receives the retained message and that Quotagent shows the expected bars and reset countdowns. Keep credentials out of MQTT payloads and logs. Ask before replacing an existing publisher or changing device settings.
