import {
  HEADER_RE,
  KEYWORDS,
  isDigit,
  isHex,
  isIdentPart,
  isIdentStart,
} from "./keywords.ts";

export type TokenKind =
  | "header"
  | "comment"
  | "string"
  | "number"
  | "ident"
  | "keyword"
  | "punct"
  | "space"
  | "newline";

export interface Token {
  kind: TokenKind;
  value: string;
}

const MULTI_PUNCT = [
  "<<=",
  ">>=",
  "::=",
  "+=",
  "-=",
  "*=",
  "/=",
  "%=",
  "&=",
  "|=",
  "^=",
  "==",
  "!=",
  "<=",
  ">=",
  "&&",
  "||",
  "..",
  "->",
  "<<",
  ">>",
];

export function tokenize(source: string): Token[] {
  const tokens: Token[] = [];
  const n = source.length;
  let i = 0;

  const push = (kind: TokenKind, value: string) => {
    tokens.push({ kind, value });
  };

  while (i < n) {
    const c = source[i]!;

    if (c === "\n") {
      push("newline", "\n");
      i += 1;
      continue;
    }
    if (c === "\r") {
      if (source[i + 1] === "\n") {
        push("newline", "\n");
        i += 2;
      } else {
        push("newline", "\n");
        i += 1;
      }
      continue;
    }

    if (c === " " || c === "\t" || c === "\f" || c === "\v") {
      const start = i;
      i += 1;
      while (i < n) {
        const s = source[i]!;
        if (s === " " || s === "\t" || s === "\f" || s === "\v") i += 1;
        else break;
      }
      push("space", source.slice(start, i));
      continue;
    }

    if (c === "#") {
      if (source[i + 1] === "-") {
        const start = i;
        i += 2;
        while (i < n && !(source[i] === "#" && source[i - 1] === "-")) {
          i += 1;
        }
        if (i < n) i += 1; // consume closing #
        push("comment", source.slice(start, i));
        continue;
      }

      const start = i;
      while (i < n && source[i] !== "\n" && source[i] !== "\r") i += 1;
      const raw = source.slice(start, i);
      if (HEADER_RE.test(raw.trim())) {
        push("header", raw.trim());
      } else {
        push("comment", raw);
      }
      continue;
    }

    if (c === '"' || c === "'") {
      const quote = c;
      const start = i;
      i += 1;
      while (i < n) {
        const ch = source[i]!;
        if (ch === "\\") {
          i += 2;
          continue;
        }
        if (ch === quote) {
          i += 1;
          break;
        }
        i += 1;
      }
      push("string", source.slice(start, i));
      continue;
    }

    if (c === "0" && (source[i + 1] === "x" || source[i + 1] === "X")) {
      const start = i;
      i += 2;
      while (i < n && isHex(source[i]!)) i += 1;
      push("number", source.slice(start, i));
      continue;
    }

    if (isDigit(c)) {
      const start = i;
      i += 1;
      while (i < n && isDigit(source[i]!)) i += 1;
      if (
        source[i] === "." &&
        source[i + 1] !== "." &&
        (isDigit(source[i + 1]!) ||
          source[i + 1] === "e" ||
          source[i + 1] === "E")
      ) {
        i += 1;
        while (i < n && isDigit(source[i]!)) i += 1;
      } else if (source[i] === "." && source[i + 1] !== "." && i + 1 === n) {
        i += 1;
      } else if (
        source[i] === "." &&
        source[i + 1] !== "." &&
        !isIdentStart(source[i + 1] ?? "")
      ) {
        // `1.` as a real, but not `1.foo`
        i += 1;
      }
      if (source[i] === "e" || source[i] === "E") {
        i += 1;
        if (source[i] === "+" || source[i] === "-") i += 1;
        while (i < n && isDigit(source[i]!)) i += 1;
      }
      push("number", source.slice(start, i));
      continue;
    }

    if (isIdentStart(c)) {
      const start = i;
      i += 1;
      while (i < n && isIdentPart(source[i]!)) i += 1;
      const value = source.slice(start, i);
      push(KEYWORDS.has(value) ? "keyword" : "ident", value);
      continue;
    }

    let matched = false;
    for (const op of MULTI_PUNCT) {
      if (source.startsWith(op, i)) {
        push("punct", op);
        i += op.length;
        matched = true;
        break;
      }
    }
    if (matched) continue;

    push("punct", c);
    i += 1;
  }

  return tokens;
}

export function isTrivia(t: Token): boolean {
  return t.kind === "space" || t.kind === "comment" || t.kind === "newline";
}
