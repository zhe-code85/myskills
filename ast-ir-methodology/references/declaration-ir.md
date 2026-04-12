# Declaration IR

Use this file when declaration extraction is failing on grouped declarators, shared heads, mixed full declarations and shorthand references, or dimension ownership.

## Split every declaration into

- declaration kind
- shared head
- item list
- source span

## Ownership

Shared head owns direction, qualifiers, data/net kind, signing, type expression, and packed/type-owned dimensions.

Each item owns the declared name, item-local suffixes, unpacked/item-owned dimensions, and initializer/default attached to that symbol.

## Hard rules

- Expand one syntactic declaration list into one IR item per symbol.
- Preserve declaration order.
- Mark inherited fields explicitly.
- Never merge multiple names into one synthetic symbol.
- Never move dimensions across head/item boundaries unless the grammar reference proves it.
