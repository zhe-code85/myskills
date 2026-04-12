# Failure patterns

Use this file when ChatGPT starts guessing or retrying.

## Common mistakes

- wrapper name reported as identifier/literal value
- operator token treated as a full expression node
- grouped declaration treated as one symbol
- packed and unpacked dimensions collapsed together
- expression text simplified during extraction
- parser-specific naming overfit into the core method

## Recovery

1. rebuild the atom table
2. restate head/item ownership
3. reconstruct source-faithful expression text
4. compare with a smaller testcase
5. move language-specific observations into a language reference
