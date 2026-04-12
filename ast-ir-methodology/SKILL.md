---
name: ast-ir-methodology
description: teach chatgpt to learn and parse ast json plus optional source text using a tool-agnostic, language-agnostic core method with language-specific references. use when chatgpt must extract declarations, identifiers, literals, dimensions, ranges, operators, expressions, or build a stable intermediate representation from unfamiliar asts; when chatgpt must generate coverage-guided source stimuli to obtain broader ast coverage; or when chatgpt keeps failing on wrapper nodes, token leaves, mixed declarations, shared declaration heads, grouped declarators, dimension ownership, source-faithful expression preservation, or unstable extractor logic.
---

Use this skill to turn unfamiliar AST JSON into stable, source-faithful observations before answering extraction questions or writing extractor code.

If the current task is blocked by repeated AST extraction failures, unknown wrapper/tag structure, identifier/literal confusion, unstable declaration parsing, poor testcase coverage, or extractor logic that keeps being patched without converging, switch into this workflow before continuing the original task.

This skill teaches a general method for learning AST JSON formats. It does not depend on any single parser or language. Use the core method first, then route into language references only when the observed behavior depends on language-specific grammar.

## Core workflow

Follow this order:

1. Inventory the AST shape.
2. Separate structural nodes from atom leaves.
3. Build a tiny parser-specific taxonomy for the current AST.
4. Normalize atoms, declarations, and expressions into a source-faithful IR.
5. Identify coverage gaps and generate minimal diagnostic stimuli if needed.
6. Load the matching language reference only if needed.
7. Answer the task from the IR, or use the IR to guide extractor implementation.

## Output target

Default to two layers:

- Layer 1: source-faithful IR and key observations.
- Layer 2: task-specific answer, extractor plan, or implementation guidance derived from the IR.

Build Layer 1 internally even when only Layer 2 is requested.

## Hard rules

- Do not begin with parser-specific assumptions, regex-like guessing, or ad hoc case lists.
- If a node has a source-text field such as `text`, prefer that as the lexeme.
- If a leaf has no text field and its tag is itself a keyword, operator, or punctuation token, treat the tag as the lexeme.
- Never report wrapper names such as `Expression`, `Reference`, `Number`, or `UnqualifiedId` as parsed identifier/literal values.
- Do not assume one declaration-shaped node equals one logical symbol.
- Expand grouped declarations into one IR item per declared symbol.
- Keep shared-head properties separate from item-owned properties.
- Preserve packed/type-owned dimensions separately from item-owned dimensions.
- Preserve expression text faithfully; do not simplify, reorder, or evaluate it during extraction.
- When AST evidence is ambiguous, compare against source text or a smaller diagnostic testcase before concluding.
- Before editing extractor logic, state the target IR, the observed ambiguities, and the acceptance checks that must pass.

## Minimal IRs

Use a compact atom IR:

```json
{"raw_tag":"...","lexeme":"...","atom_family":"identifier|literal|keyword|operator|punctuation|other","source_span":null}
```

Use a compact declaration IR:

```json
{"kind":"port|parameter|variable|field|other","head":{},"items":[{"name":"...","item_dimensions":[],"initializer":null,"derived_from_head":true}],"source_span":null}
```

## Routing

Read only the file needed for the current failure mode:

- atom/tag confusion -> `references/atom-normalization.md`
- grouped declarations / ownership confusion -> `references/declaration-ir.md`
- poor syntax coverage / testcase design -> `references/stimulus-design.md`
- turning observations into implementation guidance -> `references/extractor-guidance.md`
- repeated retries / sanity check -> `references/failure-patterns.md`
- language-specific grammar behavior -> `references/languages/README.md` then the matching language file
