#!/usr/bin/env python3
"""Check or install the project-local adaptation of Blueforcer's Berry skill."""

import argparse
import fcntl
import hashlib
import io
from itertools import zip_longest
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile


SKILL = "awtrix-berry-app"
SOURCE = "https://blueforcer.github.io/awtrix-ng/esp32/examples/awtrix-berry-app-skill.zip"
LIMIT = 2 * 1024 * 1024
TEMPLATE = Path(__file__).with_name("berry-skill.md")

# Exact headings in archive order. A new, moved or renamed heading needs review.
SECTIONS = {
    "upstream-workflow": (
        "# AWTRIX NG - Berry app builder",
        "## 1. How to answer",
    ),
    "hardware": ("## 2. The hardware",),
    "app-structure": ("## 3. The shape of every app", "## 4. Lifecycle"),
    "api-basics": ("## 5. The API",),
    "drawing": (
        "### 5.1 Panel and drawing",
        "### 5.2 Text",
        "### 5.3 Charts and progress",
        "### 5.4 Effects and overlays",
        "### 5.5 Icons",
    ),
    "time-and-input": ("### 5.6 Time", "### 5.6b Timers", "### 5.6c Button events"),
    "networking": (
        "### 5.7 HTTP",
        "### 5.7b Modbus TCP",
        "### 5.8 MQTT",
        "### 5.9 Regular expressions",
        "### 5.10 Notifications",
    ),
    "state-and-modules": (
        "### 5.11 Storage",
        "### 5.11b Settings the user can change - `@config`",
        "### 5.11c Settings several apps share",
        "### 5.12 Talking to other apps",
    ),
    "device-features": (
        "### 5.12b Sensors",
        "### 5.13 The rotation",
        "### 5.14 Display power",
        "### 5.15 Logging",
        "### 5.16 Numbers",
        "### 5.17 Device settings",
    ),
    "audio": ("### 5.18 Sound", "### 5.18b Music"),
    "script-modes": (
        "### 5.19 Running without ever being shown",
        "### 5.20 Modules: code several apps share",
    ),
    "language-and-memory": (
        "## 6. Berry language notes",
        "## 7. What is NOT available",
        "## 8. Limits",
        "## 9. Writing for a small heap",
    ),
    "panel-design": ("## 10. Designing for a 32×8 panel",),
    "example": ("## 11. Worked example",),
    "checklist": ("## 12. Check before you answer",),
    "handoff": ("## 13. What to tell the user afterwards",),
    "advanced": (
        "## Gamepad (`import gamepad`)",
        "## Bluetooth LE (`import ble`)",
        "## Hashing (`import crypto`)",
        "## Signing in (`import oauth`)",
        "## Proof of work (`import crypto`)",
        "## TCP text connections (`import tcp`)",
    ),
    "secrets": ("## API keys (`# @secret`, `import secret`)",),
    "voice": ("## Voice (`import voice`)",),
}


def split_reference(raw):
    lines = raw.decode("utf-8").splitlines(keepends=True)
    headings = []
    fence = ""
    in_api = False
    for index, line in enumerate(lines):
        marker = re.match(r" {0,3}(`{3,}|~{3,})(.*)", line)
        if fence:
            if marker and marker[1].startswith(fence) and not marker[2].strip():
                fence = ""
            continue
        if marker:
            fence = marker[1]
            continue
        heading = re.match(r" {0,3}(#{1,3})[ \t]+([^\r\n]+)", line)
        if not heading:
            continue
        level, title = heading.groups()
        label = f"{level} {title}"
        if len(level) < 3:
            in_api = label == "## 5. The API"
        if len(level) < 3 or in_api:
            headings.append((index, label))
    if fence or not headings or headings[0][0] != 0:
        raise ValueError("unexpected reference layout (title or fenced code)")

    expected = [title for group in SECTIONS.values() for title in group]
    actual = (title for _, title in headings)
    for wanted, found in zip_longest(expected, actual, fillvalue="end of document"):
        if wanted != found:
            raise ValueError(f"reference heading changed: expected {wanted!r}, found {found!r}")

    boundaries = [index for index, _ in headings] + [len(lines)]
    files = {}
    start = 0
    for name, group in SECTIONS.items():
        stop = start + len(group)
        files[f"references/{name}.md"] = "".join(lines[boundaries[start]:boundaries[stop]]).encode()
        start = stop
    return files


def generate(raw):
    entry = f"{SKILL}/SKILL.md"
    reference = f"{SKILL}/references/awtrix-api.md"
    with ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if sorted(member.filename for member in members) != sorted([entry, reference]):
            raise ValueError("unexpected ZIP contents (expected SKILL.md and references/awtrix-api.md)")
        if any(member.file_size > LIMIT for member in members):
            raise ValueError("ZIP member too large")
        upstream = archive.read(entry).decode("utf-8")
        files = split_reference(archive.read(reference))

    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", upstream, re.DOTALL)
    required = ("name: awtrix-berry-app", "license: PolyForm-Noncommercial-1.0.0", "  author: Blueforcer")
    if not frontmatter or not all(line in frontmatter[1].splitlines() for line in required):
        raise ValueError("unexpected upstream skill metadata (name, license or author changed)")
    body = TEMPLATE.read_text(encoding="utf-8")
    links = set(re.findall(r"\]\((references/[^)]+)\)", body))
    if links != files.keys():
        raise ValueError("skill index and split rules disagree")
    files["SKILL.md"] = frontmatter[0].encode() + body.encode()
    digest = hashlib.sha256(raw).hexdigest()
    files["UPSTREAM.md"] = (
        "# Upstream provenance\n\n"
        "Required Notice: Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng\n\n"
        "License: https://polyformproject.org/licenses/noncommercial/1.0.0\n\n"
        f"Official ZIP: {SOURCE}\n\n"
        f"ZIP SHA-256: `{digest}`\n\n"
        "Local adaptation: upstream skill metadata is preserved, the entry instructions are replaced, "
        "and the API reference is split verbatim.\n"
    ).encode()
    return files, digest


def current(destination, files):
    return not destination.is_symlink() and all(
        (destination / name).is_file() and (destination / name).read_bytes() == content
        for name, content in files.items()
    )


def install(destination, files):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (destination.parent / ".awtrix-berry-app.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            raise ValueError(f"expected an ordinary skill directory at {destination}")
        if current(destination, files):
            return "up to date"

        staging = Path(tempfile.mkdtemp(prefix=".berry-skill-", dir=destination.parent))
        candidate = staging / "candidate"
        previous = staging / "previous"
        had_previous = destination.exists()
        try:
            for name, content in files.items():
                path = candidate / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            if had_previous:
                destination.rename(previous)
            candidate.rename(destination)
        except BaseException:
            if previous.exists():
                try:
                    previous.rename(destination)
                except OSError as error:
                    raise OSError(f"could not restore previous skill; recover it from {previous}") from error
            shutil.rmtree(staging)
            raise
        shutil.rmtree(staging)
        return "updated" if had_previous else "installed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "install"), help="compare read-only, or install/update")
    parser.add_argument("--archive", type=Path, help="use a local official ZIP instead of downloading it")
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / ".agents" / "skills" / SKILL
    try:
        with args.archive.open("rb") if args.archive else urlopen(SOURCE, timeout=15) as source:
            raw = source.read(LIMIT + 1)
        if len(raw) > LIMIT:
            raise ValueError("ZIP too large")
        files, digest = generate(raw)
        if args.action == "check":
            ok = current(destination, files)
            result = "up to date" if ok else ("update available" if destination.exists() else "not installed")
        else:
            result = install(destination, files)
            ok = True
    except (OSError, ValueError, BadZipFile, RuntimeError) as error:
        print(f"{SKILL}: {error}", file=sys.stderr)
        return 2
    print(f"{SKILL}: {result} (ZIP SHA-256: {digest})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
