# Coverage-guided stimulus design

Use this file when current AST examples are too narrow and ChatGPT must generate small source snippets that expose more syntax with less trial-and-error.

## Principles

- Prefer a matrix of tiny cases over one giant testcase.
- Vary one syntax axis at a time.
- Keep snippets minimal so the target subtree is easy to locate.
- Include both ordinary and adversarial forms.

## Useful axes

- declaration style
- grouped list length
- shared head vs repeated full form
- packed vs unpacked dimensions
- initializer/default placement
- identifier families
- literal families
- expression families
- wrapper statements/blocks around the target syntax

## Learning loop

1. write a tiny testcase
2. locate its AST subtree
3. record wrapper chain and atom leaves
4. normalize to generic IR
5. compare against neighboring cases
6. promote confirmed patterns into the language reference
