# Domain Docs

Use when reading or recording glossary terms and architecture decisions. Domain documents are created as decisions are resolved; their absence is expected in a repo that has not recorded any yet.

## Read existing context

- Read root `CONTEXT.md` if present and the relevant decisions in `docs/adr/`.
- If `CONTEXT-MAP.md` exists, follow its pointers to the contexts relevant to the task.

Proceed with the available documents. The `/domain-modeling` skill creates glossary entries and ADRs when terms or decisions actually get resolved.

## Record new context

This repo's default layout is root `CONTEXT.md` for the glossary and `docs/adr/NNNN-<decision>.md` for ADRs. Create a context map only when distinct contexts require one; use the locations it specifies rather than assuming a `src/` tree.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

Name the conflicting ADR and explain which decision would change.
