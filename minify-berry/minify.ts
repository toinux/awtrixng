import {
  FROZEN_GLOBALS,
  FROZEN_METHODS,
  KEYWORDS,
  MODULE_HEADER_RE,
} from "./keywords.ts";
import { isTrivia, tokenize, type Token } from "./tokenize.ts";

export interface MinifyOptions {
  /** Rename locals, params, for-vars, nested defs, import aliases. Default true. */
  renameLocals?: boolean;
  /** Rename classes and top-level functions defined in the file. Default true. */
  renameClasses?: boolean;
  /** Join the body onto as few lines as possible. Default true. */
  joinLines?: boolean;
}

export interface RenameEntry {
  from: string;
  to: string;
  kind: "local" | "class" | "function" | "alias";
}

export interface MinifyReport {
  compacted: string;
  originalBytes: number;
  compactedBytes: number;
  savedBytes: number;
  savedPercent: number;
  renames: RenameEntry[];
  isModule: boolean;
}

export function byteSize(s: string): number {
  return new TextEncoder().encode(s).length;
}

type ScopeKind = "module" | "class" | "function" | "block";

interface Binding {
  original: string;
  rename: boolean;
  kind: RenameEntry["kind"];
  short?: string;
}

interface Scope {
  kind: ScopeKind;
  parent: Scope | null;
  bindings: Map<string, Binding>;
  children: Scope[];
}

function makeScope(kind: ScopeKind, parent: Scope | null): Scope {
  const scope: Scope = { kind, parent, bindings: new Map(), children: [] };
  parent?.children.push(scope);
  return scope;
}

function bind(
  scope: Scope,
  name: string,
  rename: boolean,
  kind: RenameEntry["kind"],
): void {
  if (!name || KEYWORDS.has(name)) return;
  if (scope.bindings.has(name)) return;
  if (rename && (FROZEN_METHODS.has(name) || FROZEN_GLOBALS.has(name))) {
    scope.bindings.set(name, { original: name, rename: false, kind });
    return;
  }
  scope.bindings.set(name, { original: name, rename, kind });
}

function lookup(scope: Scope | null, name: string): Binding | null {
  let cur = scope;
  while (cur) {
    const found = cur.bindings.get(name);
    if (found) return found;
    cur = cur.parent;
  }
  return null;
}

function nextCode(tokens: Token[], i: number): number {
  let j = i;
  while (j < tokens.length && isTrivia(tokens[j]!)) j += 1;
  return j;
}

function prevCode(tokens: Token[], i: number): number {
  let j = i;
  while (j >= 0 && isTrivia(tokens[j]!)) j -= 1;
  return j;
}

function isAfterDot(tokens: Token[], i: number): boolean {
  const p = prevCode(tokens, i - 1);
  return p >= 0 && tokens[p]!.kind === "punct" && tokens[p]!.value === ".";
}

function collectIdentsAfter(
  tokens: Token[],
  start: number,
): { names: string[]; end: number } {
  const names: string[] = [];
  let i = nextCode(tokens, start);
  while (i < tokens.length) {
    const t = tokens[i]!;
    if (t.kind === "ident") {
      names.push(t.value);
      i = nextCode(tokens, i + 1);
      if (
        i < tokens.length &&
        tokens[i]!.kind === "punct" &&
        tokens[i]!.value === ","
      ) {
        i = nextCode(tokens, i + 1);
        continue;
      }
      break;
    }
    break;
  }
  return { names, end: i };
}

function lambdaParams(tokens: Token[], slashIndex: number): string[] {
  let i = nextCode(tokens, slashIndex + 1);
  const params: string[] = [];
  while (i < tokens.length && tokens[i]!.kind === "ident") {
    params.push(tokens[i]!.value);
    i = nextCode(tokens, i + 1);
    if (
      i < tokens.length &&
      tokens[i]!.kind === "punct" &&
      tokens[i]!.value === ","
    ) {
      i = nextCode(tokens, i + 1);
    }
  }
  if (
    params.length > 0 &&
    i < tokens.length &&
    tokens[i]!.kind === "punct" &&
    tokens[i]!.value === "->"
  ) {
    return params;
  }
  return [];
}

function enclosingFunction(scope: Scope): Scope {
  let cur: Scope | null = scope;
  while (cur && cur.kind !== "function") cur = cur.parent;
  return cur ?? scope;
}

function enclosingClass(scope: Scope): Scope | null {
  let cur: Scope | null = scope;
  while (cur && cur.kind !== "class") cur = cur.parent;
  return cur;
}

function isModuleFile(tokens: Token[]): boolean {
  for (const t of tokens) {
    if (t.kind === "header" && MODULE_HEADER_RE.test(t.value)) return true;
    if (
      t.kind !== "header" &&
      t.kind !== "comment" &&
      t.kind !== "space" &&
      t.kind !== "newline"
    ) {
      return false;
    }
  }
  return false;
}

interface Analysis {
  root: Scope;
  identScope: (Scope | null)[];
  isModule: boolean;
}

function analyze(tokens: Token[]): Analysis {
  const root = makeScope("module", null);
  const identScope: (Scope | null)[] = new Array(tokens.length).fill(null);
  const blockStack: { kind: string; scope: Scope }[] = [
    { kind: "module", scope: root },
  ];
  let current = root;
  const isMod = isModuleFile(tokens);

  const pushBlock = (kind: string, scope: Scope) => {
    blockStack.push({ kind, scope });
    current = scope;
  };

  const popBlock = () => {
    if (blockStack.length > 1) blockStack.pop();
    current = blockStack[blockStack.length - 1]!.scope;
  };

  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i]!;
    if (t.kind === "ident") {
      identScope[i] = current;
      continue;
    }
    if (t.kind !== "keyword" && t.kind !== "punct") continue;

    if (t.kind === "punct" && t.value === "/") {
      const params = lambdaParams(tokens, i);
      if (params.length > 0) {
        const fn = enclosingFunction(current);
        for (const p of params) bind(fn, p, true, "local");
      }
      continue;
    }

    if (t.kind !== "keyword") continue;

    switch (t.value) {
      case "class": {
        const j = nextCode(tokens, i + 1);
        if (j < tokens.length && tokens[j]!.kind === "ident") {
          bind(current, tokens[j]!.value, !isMod, "class");
        }
        const body = makeScope("class", current);
        pushBlock("class", body);
        break;
      }
      case "def": {
        const methodLevel =
          enclosingFunction(current).kind !== "function" &&
          enclosingClass(current) !== null;

        let j = nextCode(tokens, i + 1);
        let fname: string | null = null;
        if (j < tokens.length && tokens[j]!.kind === "ident") {
          fname = tokens[j]!.value;
          j = nextCode(tokens, j + 1);
        }

        if (fname) {
          if (methodLevel || current.kind === "class") {
            bind(enclosingClass(current) ?? current, fname, false, "function");
          } else if (current.kind === "module") {
            bind(current, fname, !isMod, "function");
          } else {
            bind(enclosingFunction(current), fname, true, "function");
          }
        }

        const fn = makeScope("function", current);
        if (j < tokens.length && tokens[j]!.kind === "punct" && tokens[j]!.value === "(") {
          const { names } = collectIdentsAfter(tokens, j + 1);
          for (const p of names) bind(fn, p, true, "local");
        }
        pushBlock("def", fn);
        break;
      }
      case "var": {
        const { names } = collectIdentsAfter(tokens, i + 1);
        const inMethod = enclosingFunction(current).kind === "function";
        const cls = enclosingClass(current);
        if (cls && !inMethod) {
          for (const n of names) bind(cls, n, false, "local");
        } else {
          const target = enclosingFunction(current);
          for (const n of names) bind(target, n, true, "local");
        }
        break;
      }
      case "static": {
        const j = nextCode(tokens, i + 1);
        if (j < tokens.length && tokens[j]!.kind === "keyword" && tokens[j]!.value === "def") {
          break; // handled by def
        }
        const { names } = collectIdentsAfter(tokens, i + 1);
        const cls = enclosingClass(current) ?? current;
        for (const n of names) bind(cls, n, false, "local");
        break;
      }
      case "for": {
        const j = nextCode(tokens, i + 1);
        if (j < tokens.length && tokens[j]!.kind === "ident") {
          bind(enclosingFunction(current), tokens[j]!.value, true, "local");
        }
        const body = makeScope("block", current);
        pushBlock("for", body);
        break;
      }
      case "if":
      case "while":
      case "try": {
        const body = makeScope("block", current);
        pushBlock(t.value, body);
        break;
      }
      case "do": {
        const p = prevCode(tokens, i - 1);
        const prev = p >= 0 ? tokens[p]! : null;
        const attached =
          prev?.kind === "keyword" &&
          (prev.value === "if" ||
            prev.value === "while" ||
            prev.value === "for" ||
            prev.value === "elif" ||
            prev.value === "else" ||
            prev.value === "except");
        if (!attached) {
          const body = makeScope("block", current);
          pushBlock("do", body);
        }
        break;
      }
      case "import": {
        const j = nextCode(tokens, i + 1);
        if (j < tokens.length && tokens[j]!.kind === "ident") {
          const modName = tokens[j]!.value;
          const k = nextCode(tokens, j + 1);
          if (
            k < tokens.length &&
            tokens[k]!.kind === "keyword" &&
            tokens[k]!.value === "as"
          ) {
            const a = nextCode(tokens, k + 1);
            if (a < tokens.length && tokens[a]!.kind === "ident") {
              bind(current, tokens[a]!.value, true, "alias");
            }
          } else {
            bind(current, modName, false, "alias");
          }
        }
        break;
      }
      case "as": {
        const a = nextCode(tokens, i + 1);
        if (a < tokens.length && tokens[a]!.kind === "ident") {
          const already = lookup(current, tokens[a]!.value);
          if (!already) bind(enclosingFunction(current), tokens[a]!.value, true, "local");
        }
        break;
      }
      case "end": {
        popBlock();
        break;
      }
      default:
        break;
    }
  }

  // Implicit locals: ident = inside a function, not after a dot, not already bound
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i]!;
    if (t.kind !== "ident") continue;
    if (isAfterDot(tokens, i)) continue;
    const scope = identScope[i];
    if (!scope) continue;
    const fn = enclosingFunction(scope);
    if (fn.kind !== "function") continue;
    if (!isDeclarationEquals(tokens, i)) continue;

    if (lookup(scope, t.value)) continue;
    if (FROZEN_GLOBALS.has(t.value) || FROZEN_METHODS.has(t.value)) continue;
    if (KEYWORDS.has(t.value)) continue;
    bind(fn, t.value, true, "local");
  }

  return { root, identScope, isModule: isMod };
}

function* shortNameGen(): Generator<string> {
  const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
  for (const c of letters) yield c;
  let n = 0;
  for (;;) {
    const i = n++;
    const letter = letters[i % letters.length]!;
    const num = Math.floor(i / letters.length);
    yield `${letter}${num}`;
  }
}

function isDeclarationEquals(tokens: Token[], identIndex: number): boolean {
  let j = identIndex;
  while (j < tokens.length) {
    if (tokens[j]!.kind !== "ident") return false;
    j = nextCode(tokens, j + 1);
    if (j >= tokens.length) return false;
    const t = tokens[j]!;
    if (t.kind === "punct" && t.value === "=") return true;
    if (t.kind === "punct" && t.value === ",") {
      j = nextCode(tokens, j + 1);
      continue;
    }
    return false;
  }
  return false;
}

function collectFrozenOriginals(tokens: Token[], root: Scope): Set<string> {
  const frozen = new Set<string>([...KEYWORDS, ...FROZEN_GLOBALS, ...FROZEN_METHODS]);
  const visit = (s: Scope) => {
    for (const b of s.bindings.values()) {
      if (!b.rename) frozen.add(b.original);
    }
    for (const c of s.children) visit(c);
  };
  visit(root);
  for (const t of tokens) {
    if (t.kind === "ident" && (FROZEN_GLOBALS.has(t.value) || FROZEN_METHODS.has(t.value))) {
      frozen.add(t.value);
    }
  }
  return frozen;
}

function assignShorts(scope: Scope, taken: Set<string>): void {
  const gen = shortNameGen();
  const localTaken = new Set(taken);
  for (const b of scope.bindings.values()) {
    if (!b.rename) {
      localTaken.add(b.original);
      continue;
    }
    let next = gen.next().value;
    while (
      localTaken.has(next) ||
      taken.has(next) ||
      KEYWORDS.has(next) ||
      FROZEN_GLOBALS.has(next) ||
      FROZEN_METHODS.has(next)
    ) {
      next = gen.next().value;
    }
    b.short = next;
    localTaken.add(next);
  }
  for (const child of scope.children) {
    assignShorts(child, localTaken);
  }
}

function wordish(t: Token): boolean {
  return t.kind === "ident" || t.kind === "keyword" || t.kind === "number";
}

function needsSpace(prev: Token, next: Token): boolean {
  if (prev.kind === "header") return false;
  if (wordish(prev) && wordish(next)) return true;
  // `end#` is fine; `0x` already one token
  // Keep space before unary `!`? `foo!bar` isn't valid anyway
  if (prev.kind === "number" && next.kind === "ident") return true;
  if (prev.kind === "ident" && next.kind === "number") return true;
  return false;
}

function emit(
  tokens: Token[],
  identScope: (Scope | null)[],
  options: Required<MinifyOptions>,
): { text: string; renames: RenameEntry[] } {
  const renameOn = options.renameLocals || options.renameClasses;
  const seen = new Map<string, RenameEntry>();
  const parts: string[] = [];
  let last: Token | null = null;

  const mapped = (i: number, t: Token): string => {
    if (!renameOn || t.kind !== "ident") return t.value;
    if (isAfterDot(tokens, i)) return t.value;
    const scope = identScope[i];
    const b = lookup(scope ?? null, t.value);
    if (!b || !b.rename || !b.short) return t.value;
    if (b.kind === "local" && !options.renameLocals) return t.value;
    if ((b.kind === "class" || b.kind === "function") && !options.renameClasses) {
      return t.value;
    }
    if (b.kind === "alias" && !options.renameLocals) return t.value;
    const key = `${b.kind}:${b.original}:${b.short}`;
    if (!seen.has(key)) {
      seen.set(key, { from: b.original, to: b.short, kind: b.kind });
    }
    return b.short;
  };

  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i]!;
    if (t.kind === "comment" || t.kind === "space") continue;

    if (t.kind === "header") {
      if (parts.length && parts[parts.length - 1] !== "\n") parts.push("\n");
      parts.push(t.value, "\n");
      last = t;
      continue;
    }

    if (t.kind === "newline") {
      if (!options.joinLines) {
        if (last && last.kind !== "header" && last.kind !== "newline") {
          parts.push("\n");
          last = t;
        }
      }
      continue;
    }

    const value = t.kind === "ident" ? mapped(i, t) : t.value;
    const outTok: Token = { kind: t.kind, value };
    if (last && needsSpace(last, outTok)) parts.push(" ");
    parts.push(value);
    last = outTok;
  }

  let text = parts.join("");
  text = text.replace(/[ \t]+\n/g, "\n").replace(/\n{2,}/g, "\n");
  if (text.length > 0 && !text.endsWith("\n")) text += "\n";
  return { text, renames: [...seen.values()] };
}

export function minifyBerry(source: string, opts: MinifyOptions = {}): MinifyReport {
  const options: Required<MinifyOptions> = {
    renameLocals: opts.renameLocals ?? true,
    renameClasses: opts.renameClasses ?? true,
    joinLines: opts.joinLines ?? true,
  };

  const tokens = tokenize(source);
  const { root, identScope, isModule } = analyze(tokens);

  if (options.renameLocals || options.renameClasses) {
    const frozen = collectFrozenOriginals(tokens, root);
    assignShorts(root, frozen);
  }

  const { text, renames } = emit(tokens, identScope, options);
  const originalBytes = byteSize(source);
  const compactedBytes = byteSize(text);
  const savedBytes = originalBytes - compactedBytes;
  const savedPercent = originalBytes === 0 ? 0 : (savedBytes / originalBytes) * 100;

  return {
    compacted: text,
    originalBytes,
    compactedBytes,
    savedBytes,
    savedPercent,
    renames,
    isModule,
  };
}

export function compactBerry(source: string, opts?: MinifyOptions): string {
  return minifyBerry(source, opts).compacted;
}
