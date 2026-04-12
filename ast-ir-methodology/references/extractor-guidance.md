# Analysis to extractor guidance

Use this file when ChatGPT must turn AST observations into extractor logic with less trial-and-error.

## Before writing or patching code

State these items explicitly:

1. input unit: what subtree or list the extractor consumes
2. logical output unit: what counts as one extracted symbol
3. wrapper policy: which nodes are structural only
4. atom policy: how lexemes are recovered
5. ownership policy: which properties belong to shared head vs individual item
6. preservation policy: which expressions and spans must remain source-faithful
7. uncertainty list: which observed forms still need more coverage

## Acceptance-first workflow

Define acceptance checks before editing code.

Useful checks:

- one logical symbol per declared name
- grouped declarations preserve every symbol in order
- inherited properties stay attached to later symbols when syntax omits repetition
- packed/type-owned and item-owned dimensions stay separated
- expression text is preserved without evaluation or rewriting
- unknown shapes are surfaced explicitly instead of guessed

## Implementation guidance

- Implement from the normalized IR outward, not from raw tags inward.
- Prefer role-based classification over one-off tag checks.
- Use minimal diagnostic stimuli to validate each new rule.
- When one observed shape suggests a rule, test at least one neighboring variant before generalizing it.
