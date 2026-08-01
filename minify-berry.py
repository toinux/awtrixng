#!/usr/bin/env python3
"""
minify_berry.py - shrink a Berry (.be) source file for AWTRIX NG.

Usage:
    python3 minify_berry.py script.be > script.min.be

What it does (all string-literal-safe: it never touches text inside
single or double quotes, so URLs, RTTTL strings, "#" in a string, etc.
are left exactly as written):

  1. Strips comments ("# ..." to end of line) -- EXCEPT lines whose
     comment is metadata for the AWTRIX web UI (# @name, # @config, ...).
     Those are kept byte-for-byte, because they are not documentation,
     they are read by the firmware to build the app list and settings UI.
  2. Removes leading/trailing whitespace on every line.
  3. Collapses runs of internal spaces/tabs down to a single space.
  4. Drops now-empty lines.

It does NOT try to join everything onto one line or remove newlines:
Berry statements are newline-separated (blocks are closed with `end`,
not by indentation), so collapsing across lines is not needed for size
and would risk merging tokens. This script only removes bytes that
carry no meaning, and is safe to run on any valid Berry source.

Assumption: no multi-line string literals (none appear anywhere in the
AWTRIX Berry API/doc, and the language reference gives no syntax for
them). If a script ever uses one, treat that file as unsupported.
"""
import sys


def _is_meta_comment(line: str) -> bool:
    """True for '# @xxx' header lines (@name, @desc, @config, ...)."""
    s = line.lstrip()
    if not s.startswith('#'):
        return False
    s = s[1:].lstrip()
    return s.startswith('@')


def _process_line(line: str) -> str:
    """Strip a real comment and collapse whitespace, respecting strings."""
    out = []
    in_str = None       # None, or the active quote character
    pending_space = False
    i, n = 0, len(line)

    while i < n:
        c = line[i]

        if in_str:
            out.append(c)
            if c == '\\' and i + 1 < n:      # keep escaped char verbatim
                out.append(line[i + 1])
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue

        if c == '"' or c == "'":
            if pending_space and out:
                out.append(' ')
            pending_space = False
            in_str = c
            out.append(c)
            i += 1
            continue

        if c == '#':
            break                             # real comment: drop the rest

        if c in ' \t':
            pending_space = True
            i += 1
            continue

        if pending_space and out:
            out.append(' ')
        pending_space = False
        out.append(c)
        i += 1

    return ''.join(out).strip()


def minify(text: str) -> str:
    out_lines = []
    for line in text.split('\n'):
        if _is_meta_comment(line):
            kept = line.strip()
            if kept:
                out_lines.append(kept)
            continue
        processed = _process_line(line)
        if processed:
            out_lines.append(processed)
    return '\n'.join(out_lines) + '\n'


def main():
    if len(sys.argv) != 2:
        print("usage: minify_berry.py <script.be>", file=sys.stderr)
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    except OSError as e:
        print(f"error: cannot read {sys.argv[1]}: {e}", file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(minify(text))


if __name__ == '__main__':
    main()
