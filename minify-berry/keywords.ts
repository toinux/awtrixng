/** Berry reserved words — lexer `token_strings` in berry-lang/berry. */
export const KEYWORDS = new Set([
  "if",
  "elif",
  "else",
  "while",
  "for",
  "def",
  "end",
  "class",
  "break",
  "continue",
  "return",
  "true",
  "false",
  "nil",
  "var",
  "do",
  "import",
  "as",
  "try",
  "except",
  "raise",
  "static",
]);

/**
 * Names that must never be rewritten: language specials, Berry stdlib,
 * and the AWTRIX NG host API. Implicit assignments to these stay global.
 */
export const FROZEN_GLOBALS = new Set([
  "self",
  "super",
  "nil",
  "true",
  "false",
  "print",
  "format",
  "int",
  "real",
  "bool",
  "str",
  "bytes",
  "size",
  "type",
  "classname",
  "classof",
  "isinstance",
  "number",
  "map",
  "list",
  "range",
  "module",
  "globals",
  "compiled",
  "gc",
  "input",
  "assert",
  "open",
  "json",
  "math",
  "string",
  "time",
  "os",
  "debug",
  "introspect",
  "solidify",
  "undefined",
  "comptr",
  "comobj",
  "function",
  "instance",
  "class",
  "bool",
  // AWTRIX NG host objects / modules
  "store",
  "http",
  "mqtt",
  "re",
  "rotation",
  "sensor",
  "settings",
  "shared",
  "sound",
  "log",
  "notify",
  "num",
  "round",
  "clamp",
  "min",
  "max",
  "width",
  "height",
  "clear",
  "pixel",
  "line",
  "rect",
  "rect_fill",
  "circle",
  "circle_fill",
  "rgb",
  "hsv",
  "text",
  "text_width",
  "text_ink_width",
  "font",
  "ramp_text",
  "scroll_text",
  "bar_chart",
  "line_chart",
  "progress",
  "effect",
  "overlay",
  "icon",
  "hour",
  "minute",
  "second",
  "weekday",
  "day",
  "month",
  "year",
  "epoch_ms",
  "now_ms",
  "version",
]);

/** Class methods the VM or AWTRIX call by name — never rename. */
export const FROZEN_METHODS = new Set([
  "init",
  "deinit",
  "tostring",
  "setup",
  "draw",
  "loop",
  "on_show",
  "on_hide",
  "on_button",
  "should_show",
  "duration",
  "item",
  "setitem",
  "member",
  "setmember",
  "call",
  "add",
  "sub",
  "mul",
  "div",
  "mod",
  "and",
  "or",
  "xor",
  "lsh",
  "rsh",
  "neg",
  "flip",
  "lt",
  "le",
  "eq",
  "ne",
  "gt",
  "ge",
]);

export const HEADER_RE =
  /^#\s*@(name|desc|author|version|headless|module|config)\b/i;

export const MODULE_HEADER_RE = /^#\s*@module\b/i;

export function isIdentStart(ch: string): boolean {
  return (ch >= "A" && ch <= "Z") || (ch >= "a" && ch <= "z") || ch === "_";
}

export function isIdentPart(ch: string): boolean {
  return isIdentStart(ch) || (ch >= "0" && ch <= "9");
}

export function isDigit(ch: string): boolean {
  return ch >= "0" && ch <= "9";
}

export function isHex(ch: string): boolean {
  return (
    (ch >= "0" && ch <= "9") ||
    (ch >= "a" && ch <= "f") ||
    (ch >= "A" && ch <= "F")
  );
}
