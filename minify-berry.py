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
  4. Drops the (now single) space entirely when it sits next to a
     "safe" punctuation character: ( ) [ ] { } , ; :
     These characters are never part of an identifier, a number or a
     multi-char operator, so removing the space beside them can never
     merge two tokens into a different one (unlike, say, collapsing
     "a - -1" into "a--1" next to an operator, which this script does
     NOT do, on purpose).
  5. Drops now-empty lines.

It does NOT try to join everything onto one line or remove newlines:
Berry statements are newline-separated (blocks are closed with `end`,
not by indentation), so collapsing across lines is not needed for size
and would risk merging tokens. It also does NOT touch whitespace around
operators (=, +, -, *, /, ==, &&, ->, .., ...) or around `.`, since
those characters combine into different multi-char tokens or interact
with number literals, and the size win is not worth the risk.

Assumption: no multi-line string literals (none appear anywhere in the
AWTRIX Berry API/doc, and the language reference gives no syntax for
them). If a script ever uses one, treat that file as unsupported.
"""
import sys

# Punctuation next to which a space can always be dropped without any
# risk of merging tokens: none of these combine with a neighbouring
# character to form a different operator or literal.
NO_SPACE_CHARS = set("(){}[],;:")


def _is_meta_comment(line: str) -> bool:
    """True for '# @xxx' header lines (@name, @desc, @config, ...)."""
    s = line.lstrip()
    if not s.startswith('#'):
        return False
    s = s[1:].lstrip()
    return s.startswith('@')


def _process_line(line: str) -> str:
    """Strip a real comment and collapse/drop whitespace, respecting strings."""
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
            if pending_space and out and out[-1] not in NO_SPACE_CHARS:
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

        if c in NO_SPACE_CHARS:
            # drop any space pending before this punctuation, and don't
            # let a space be re-added after it either (handled below via
            # the out[-1] check when the next real char is emitted)
            pending_space = False
            out.append(c)
            i += 1
            continue

        if pending_space and out and out[-1] not in NO_SPACE_CHARS:
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