# AGENTS.md

## Hard rule

- **Never `git commit` or `git push` without the user's explicit approval.** No exceptions, even for changes made at their request.

## What this repo is

- Independent AWTRIX NG apps live in `apps/<app>/`, each with an `awtrix.toml` and Berry source at `src/<app>.ax`.
- Root-level `<app>.ax` paths are compatibility symlinks for legacy callers. `deploy.sh` now reads the project source directly and delegates minification and upload to `awtrix-cli`.
- No local Berry interpreter or automated Berry compile suite is available. GitHub Actions publishes releases; Python tools exercise the physical display. The device is the compiler.
- Each source has its own semver `# @version`. Releases are independent per app via `<app>-vX.Y.Z` tags (e.g., `anothertime-v1.4.0`). The workflow validates the tag against the source header and publishes that app's minified asset.
- When bumping a source version, update `# @version`, the README script table and relevant user-facing descriptions. Stable tags must match the source version; prerelease tags may add a suffix (for example, `tesla-v1.6.0-rc.1`).
- `project.version` is required manifest metadata; release versions come from the source `# @version` and tag.

## Commands

- **Validate a project (offline):**
  ```sh
  awtrix-cli --json project validate --manifest apps/anothertime/awtrix.toml
  awtrix-cli --json project validate --manifest apps/tesla/awtrix.toml
  ```
  - Project setup and installation guidance: `README.md#development`.

- **Minify a source:**
  ```sh
  awtrix-cli minify apps/anothertime/src/anothertime.ax
  ```
  - `awtrix-cli minify` writes `anothertime.min.ax` beside the source without changing it. `*.min.ax` are generated artifacts — never commit them (see `.gitignore`).

- **Deploy (local development):**
  ```sh
  ./deploy.sh anothertime
  ```
  - Reads `AWTRIX_IP` (and optional `AWTRIX_AUTH`) from `.env` (copy `.env.example` → `.env`).
  - Uses `awtrix-cli script deploy --minify` with the source under `apps/<app>/src/`. Deployment is create-only by default. Pass `--force` to replace an installed app; this is unconditional and does not protect concurrent remote changes.
  - **Obtain deployment permission before changing the physical device.** Existing permission covers deployments and mockups within the scope the user granted.

- **Release (automated):**
  - After explicit push approval, push a tag such as `anothertime-v1.4.0` or `tesla-v1.6.0-rc.1`.
  - GitHub Actions downloads checksum-verified awtrix-cli v0.3.1, minifies only the tagged app, verifies the source version, generates release notes since its previous app tag, and publishes a `<app>-<version>.ax` asset.
  - Review the pinned awtrix-cli version periodically and update it deliberately. Release publishing requires job-level `contents: write`.

- **Verify an install:** a script that fails to compile still returns `200` — the only success is `"error": null` in the response body. To check what it draws:
  ```sh
  curl -sX PUT "http://$AWTRIX_IP/api/v1/apps/active" -H 'Content-Type: application/json' -d '{"name":"Anothertime","fast":true}'
  curl -s "http://$AWTRIX_IP/api/v1/display/screen"
  ```
  - `401` means auth is on → `curl -u user:pass`.
  - Read the installed app's config; saved choices override header defaults. Capture with `python3 tools/awtrix-screen.py --app Anothertime --wait 0.3 --out /tmp/opencode/anothertime.png` and confirm the intended app is active.

## Refactoring safely

- Before a rename/restructure, minify a baseline with `awtrix-cli`, edit, minify again and compare.
- Run `awtrix-cli minify` after every `.ax` edit. Successful minification does **not** establish valid Berry syntax. Compilation is verified only by the device's `error: null`, followed by runtime and framebuffer checks.

## Minifier constraints

- The minifier only rewrites class-field references written literally as `self.field`; alias access such as `widget.field` is not renamed and can break output. Check alias-style field access before refactoring fields.
- Class methods are not renamed. Keep method definitions and call sites synchronized; `init`, `loop` and `draw` are firmware entry points and must retain their names.
- Avoid local names that shadow AWTRIX globals.
- Keep `# @` metadata in the leading header block so the device and minifier can read it.

## Script conventions (AWTRIX-specific)

- Read `.agents/skills/awtrix-berry-app/SKILL.md` and its `references/awtrix-api.md` before writing or changing a `.ax` file. If the installed skill is missing, follow `README.md#agent-setup`. That skill is the source of truth for the API, install and verification flow.
- Header tags (`# @name`, `# @version`, `# @config …`) must stay at the top of the file: the parser stops reading tags at the first line that is neither blank nor a comment, so they cannot sit below the `import`.
- Anything the user might change is a `# @config` field read with `store.get(key)` — never a hardcoded constant, and never repeat the default in code.
- AWTRIX NG v1.1.1+ has no fixed script-size cap; older limits in the installed skill do not apply to those versions. The shared Berry heap is 96 KB without PSRAM. Installation requires contiguous source memory plus compile headroom (roughly 8 KB); `507` indicates insufficient or fragmented memory. Use minified deployment first, then consider a reboot with device-change permission. Get current source-size statistics from the minifier rather than cached byte counts.
- **Config namespace:** Each script's `@config` keys live in its own app store (`Anothertime.sc` ≠ `Weather.sc`). No prefix needed.

## Troubleshooting references

- **Tesla:** Read `docs/agents/tesla-mqtt.md` for missing TeslaMate values, subscription changes or display mockups.

## Setup

For a fresh clone or missing AWTRIX skill, follow `README.md#agent-setup`.

## Agent skills

### Issue tracker

**Issues:** Read `docs/agents/issue-tracker.md` when publishing specs, triaging tickets or managing wayfinder dependencies.

### Triage labels

**Labels:** Read `docs/agents/triage-labels.md` before assigning triage roles.

### Domain docs

**Domain:** Read `docs/agents/domain.md` when consuming or creating glossary entries or ADRs.

### GitHub Actions

Preserve SHA-pinned actions, `persist-credentials: false`, explicit permissions and environment pass-through for shell inputs when editing `.github/workflows/release.yml`.
