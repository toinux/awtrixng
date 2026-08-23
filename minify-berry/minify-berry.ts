#!/usr/bin/env -S node --experimental-strip-types
// minify-berry — CLI de minification pour scripts Berry (AWTRIX NG)
//
// Usage:
//   ./minify-berry script.ax [--variables] [--classes] [--lines] [--full] > compact.ax
//
// Options:
//   --variables   renomme les locales, paramètres, boucles for, alias d'import
//   --classes     renomme les classes et fonctions top-level
//   --lines       compacte le corps sur un minimum de lignes
//   --full        équivaut à --variables --classes --lines
//
// Sans option, seuls les commentaires et les espaces superflus sont retirés
// (aucun renommage, aucune fusion de lignes).
//
// La sortie minifiée est écrite sur stdout ; les infos (octets économisés,
// renommages) sont écrites sur stderr, pour ne pas polluer une redirection
// du type `> compact.ax`.

import { readFileSync } from "node:fs";
import { minifyBerry } from "./minify.ts";

function usage(): never {
  console.error(
    "Usage: minify-berry <fichier.ax> [--variables] [--classes] [--lines] [--full]",
  );
  process.exit(1);
}

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith("--")));
const files = args.filter((a) => !a.startsWith("--"));

if (files.length !== 1) usage();

const known = new Set(["--variables", "--classes", "--lines", "--full"]);
for (const f of flags) {
  if (!known.has(f)) {
    console.error(`Option inconnue : ${f}`);
    usage();
  }
}

const full = flags.has("--full");
const renameLocals = full || flags.has("--variables");
const renameClasses = full || flags.has("--classes");
const joinLines = full || flags.has("--lines");

const [file] = files;
let source: string;
try {
  source = readFileSync(file!, "utf8");
} catch (err) {
  console.error(`Impossible de lire ${file} : ${(err as Error).message}`);
  process.exit(1);
}

const report = minifyBerry(source, { renameLocals, renameClasses, joinLines });

process.stdout.write(report.compacted);

console.error(
  `${file}: ${report.originalBytes} -> ${report.compactedBytes} octets ` +
    `(-${report.savedPercent.toFixed(1)}%, ${report.renames.length} renommage(s))`,
);
