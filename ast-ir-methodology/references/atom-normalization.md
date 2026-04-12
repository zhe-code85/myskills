# Atom normalization

Use this file when Identifier/Literal parsing is unstable, wrapper nodes are being mistaken for values, or some tags are category names while others are raw tokens.

## Decision order

1. Wrapper or leaf?
2. If a text-like field exists, use it as the lexeme.
3. Else if the leaf tag is itself a keyword/operator/punctuation token, use the tag as the lexeme.
4. Else keep descending until a source-faithful leaf is found.

## Atom classes

- kind-tagged atom: category in `tag`, spelling in `text`
- lexeme-tagged atom: `tag` is the spelling
- wrapper node: structural region, not a lexeme

## Hard rules

- Always keep both `raw_tag` and `lexeme`.
- Never use wrapper names as identifier/literal text.
- Infer semantics from parent structure, not token spelling alone.
- Defer operator/punctuation meaning until the parent construct is known.
