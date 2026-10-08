# AGENTS.md

## Hard rule

- **Never `git commit` or `git push` without the user's explicit approval.** No exceptions, even for changes made at their request.

## What this repo is

- Independent AWTRIX NG Berry projects under `apps/`; each has an `awtrix.toml` and a source under `src/`.
- No package manager, local Berry interpreter or automated Berry compile suite. GitHub Actions publishes releases; Python tools exercise the physical display. The device is the compiler.
- Each source has its own semver `# @version` in the header. Releases are **per application** via Git tags `<script>-vX.Y.Z` (e.g., `anothertime-v1.4.0`). The workflow validates the tag against the header and publishes the minified asset on tag push.
- When bumping a script's version, update its `# @version`, README script table and relevant user-facing description; stable tags must match the source version.

## Commands

- **Minify (single script):**
  ```sh
  awtrix-cli minify apps/anothertime/src/anothertime.ax
  ```
  - Minification and project setup instructions: `README.md#development`.
  - `awtrix-cli minify` writes `anothertime.min.ax` beside its source. `*.min.ax` are generated artifacts — never commit them (see `.gitignore`).

- **Deploy (local development):**
  ```sh
  ./deploy.sh anothertime
  ```
  - Reads `AWTRIX_IP` (and optional `AWTRIX_AUTH`) from `.env` (copy `.env.example` → `.env`).
  - Minifies `<script>.ax` to generated `<script>.min.ax`, PUTs to `http://$AWTRIX_IP/api/v1/apps/script/<AppName>` where `<AppName>` = PascalCase of script name (`anothertime` → `Anothertime`).
  - **Obtain deployment permission before changing the physical device.** Existing permission covers deployments and mockups within the scope the user granted.

- **Release (automated):**
  - After explicit push approval, push a tag such as `anothertime-v1.4.0` or `tesla-v1.6.0-rc.1`.
  - GitHub Actions downloads checksum-verified awtrix-cli v0.3.1, minifies only that app, verifies the source version, generates release notes since its previous script tag, and publishes a `<script>-<version>.ax` asset.
  - Review the pinned awtrix-cli version periodically and update it deliberately. Release publishing requires job-level `contents: write`.

- **Verify an install:** a script that fails to compile still returns `200` — the only success is `"error": null` in the response body. To check what it draws:
  ```sh
  curl -sX PUT "http://$AWTRIX_IP/api/v1/apps/active" -H 'Content-Type: application/json' -d '{"name":"Anothertime","fast":true}'
  curl -s "http://$AWTRIX_IP/api/v1/display/screen"
  ```
  - `401` means auth is on → `curl -u user:pass`.
  - Read the installed app's config; saved choices override header defaults. Capture with `python3 tools/awtrix-screen.py --app Anothertime --wait 0.3 --out /tmp/opencode/anothertime.png` and confirm the intended app is active.

## Refactoring safely

- Before a rename/restructure: minify a baseline, edit, minify again and compare. Pure field/local renames should be byte-identical when binding order is unchanged; method renames and structural changes can change the output.
- Run the minifier after every `.ax` edit. It tokenizes and rewrites source; successful minification does **not** establish valid Berry syntax. Compilation is verified only by the device's `error: null`, followed by runtime and framebuffer checks.

## Minifier traps

- `--variables` rewrites class fields only where they appear literally as `self.field`. Aliased access (`def helper(w) return w.url end`) is **not** renamed → the minified script breaks. Grep for alias-style field access first.
- Class methods are never renamed (bound `rename=false` in `minify.ts`): a source rename only needs the definition and every `self.` call site changed together. `init`, `loop`, `draw` are called by name by the firmware — never rename them.
- Never name a local after an AWTRIX global (`progress`, `now_ms`, `day`, … see `FROZEN_GLOBALS` in `minify-berry/keywords.ts`): it shadows the global and the minifier leaves it unrenamed.
- Header-like comment lines survive minification and split `var` regrouping. Keep `@`-tags in the leading header; `HEADER_RE` is defined in `minify-berry/keywords.ts` and used by `tokenize.ts`.

## Script conventions (AWTRIX-specific)

- Read `.agents/skills/awtrix-berry-app/SKILL.md` and its `references/awtrix-api.md` before writing or changing a `.ax` file. That skill is the source of truth for the API, install and verification flow.
- Header tags (`# @name`, `# @version`, `# @config …`) must stay at the top of the file: the parser stops reading tags at the first line that is neither blank nor a comment, so they cannot sit below the `import`.
- Anything the user might change is a `# @config` field read with `store.get(key)` — never a hardcoded constant, and never repeat the default in code.
- AWTRIX NG v1.1.1+ has no fixed script-size cap; older limits in the installed skill do not apply to those versions. The shared Berry heap is 96 KB without PSRAM. Installation requires contiguous source memory plus compile headroom (roughly 8 KB); `507` indicates insufficient or fragmented memory. Use minified deployment first, then consider a reboot with device-change permission. Get current source-size statistics from the minifier rather than cached byte counts.
- **Config namespace:** Each script's `@config` keys live in its own app store (`Anothertime.sc` ≠ `Weather.sc`). No prefix needed.

## Troubleshooting references

- **Tesla:** Read `docs/agents/tesla-mqtt.md` for missing TeslaMate values, subscription changes or display mockups.

## Setup

For a fresh clone or missing AWTRIX skill, follow `README.md#development`.

## Agent skills

### Issue tracker

**Issues:** Read `docs/agents/issue-tracker.md` when publishing specs, triaging tickets or managing wayfinder dependencies.

### Triage labels

**Labels:** Read `docs/agents/triage-labels.md` before assigning triage roles.

### Domain docs

**Domain:** Read `docs/agents/domain.md` when consuming or creating glossary entries or ADRs.

### GitHub Actions

Preserve SHA-pinned actions, `persist-credentials: false`, explicit permissions and environment pass-through for shell inputs when editing `.github/workflows/release.yml`.
