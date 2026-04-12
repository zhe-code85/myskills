# Language routing

Use a language file only after the core method has identified a real language-dependent ambiguity.

Route here for:

- declaration forms that differ by language
- literal families and token spellings
- ownership rules for dimensions, suffixes, or type modifiers
- grammar constructs whose AST wrappers are language-specific

Suggested workflow:

1. finish the core inventory and IR sketch
2. name the unresolved ambiguity
3. open the matching language file
4. import only the language-specific rule needed to resolve that ambiguity
5. keep the extracted IR format language-neutral unless the task requires otherwise
