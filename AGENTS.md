# AGENTS.md

## Hard rule

- **Never `git commit` or `git push` without the user's explicit approval.** No exceptions, even for changes made at their request.

## What this repo is

- Berry scripts for AWTRIX NG (ESP32 32x8 LED clock). One product: `anothertime.ax`.
- No package manager, no build, no tests, no lint, no CI. The device is the only compiler — there is no local Berry interpreter.
- `README.md` is user-facing docs for the same script. When bumping a version, update `# @version` in the script and the README version table together; releases are `Release X.Y` commits.

## Commands

- **Minify:** `./minify-berry/minify-berry.ts --classes --variables anothertime.ax > compact.ax`
  - Runs via its shebang (`node --experimental-strip-types`), Node 26 through mise, zero deps, no install step.
  - Minified source goes to stdout; size/rename stats go to stderr. `compact.ax` is a generated artifact — never commit it (there is no `.gitignore`).
- **Deploy:** `./deploy.sh` = minify + `PUT` to `http://192.168.1.202/api/v1/apps/script/Anothertime` (hardcoded LAN IP, script name is case-sensitive).
  - **Ask the user before pushing anything to the physical device.**
- **Verify an install:** a script that fails to compile still returns `200` — the only success is `"error": null` in the response body. To check what it draws: `PUT /api/v1/apps/active {"name":"Anothertime","fast":true}` then `GET /api/v1/display/screen`. `401` means auth is on → `curl -u user:pass`.
  - Widgets dwell 3 s each: poll the screen every ~2 s for ~15 s to catch all four, told apart by their icon colors (temperature `#FF4C50` bulb, humidity shades `#D5F6FF`→`#0089CD`, battery green rows, calendar block).
  - Never verify against the header `default=` values — the device store keeps whatever the user configured (this device runs `dsty=calendar`, not the `icon` default).

## Refactoring safely

- Before a rename/restructure: minify the current file to a baseline, edit, minify again, `diff`. The minifier renames fields and locals itself, so a safe refactor comes out **byte-identical except for the changes you intended**. Method names pass through unchanged and will show up in the diff.
- The minifier is the only parser available locally — run it after every edit, even when not deploying; it fails on malformed Berry.

## Minifier traps

- `--variables` rewrites class fields only where they appear literally as `self.field`. Aliased access (`def helper(w) return w.url end`) is **not** renamed → the minified script breaks. Grep for alias-style field access first.
- Class methods are never renamed (bound `rename=false` in `minify.ts`): a source rename only needs the definition and every `self.` call site changed together. `init`, `loop`, `draw` are called by name by the firmware — never rename them.
- Never name a local after an AWTRIX global (`progress`, `now_ms`, `day`, … see `FROZEN_GLOBALS` in `minify-berry/keywords.ts`): it shadows the global and the minifier leaves it unrenamed.
- A comment line whose trimmed text starts with `# @name/@desc/@author/@version/@headless/@module/@config` is tokenized as a **header tag** (`HEADER_RE` in `tokenize.ts`): it survives minification and splits the `var` regrouping. Keep `@`-tags only in the header block.

## Script conventions (AWTRIX-specific)

- Read `~/.agents/skills/awtrix-berry-app/SKILL.md` and its `references/awtrix-api.md` before writing or changing a `.ax` file. That skill is the source of truth for the API, install and verification flow. The in-repo copy under `.agents/skills/` is a deprecated mirror — ignore it.
- Header tags (`# @name`, `# @version`, `# @config …`) must stay at the top of the file: the parser stops reading tags at the first line that is neither blank nor a comment, so they cannot sit below the `import`.
- Anything the user might change is a `# @config` field read with `store.get(key)` — never a hardcoded constant, and never repeat the default in code.
- Size is still a memory constraint: 96 KB shared Berry heap. AWTRIX NG v1.1.1+ has **no fixed script size cap** — `scriptMaxBytes` and the `413` it produced are gone, so an install only needs ~8 KB plus the source free, in one contiguous block; over that it answers `507 insufficientStorage` (*"script source exceeds the N bytes free to receive it"*). Source is **16862 B**, minified **7444 B** — keep new comments and renames lean anyway: the compile must hold the whole source in one block. Comments are stripped by the minifier, so commenting the source is free in the deployed script (7.4 KB); if an install returns `507` for size or fragmentation, deploy the minified output (`./deploy.sh`) or reboot to defragment.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (`toinux/awtrixng`), driven by the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` at the root plus `docs/adr/`. See `docs/agents/domain.md`.
