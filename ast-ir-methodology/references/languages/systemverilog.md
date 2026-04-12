# SystemVerilog reference

Use this file for SystemVerilog and closely related Verilog-family ASTs.

## High-value ambiguity zones

- ANSI-style port declarations with grouped names
- non-ANSI declarations and later type attachment
- packed dimensions versus unpacked dimensions
- net kind, variable kind, signing, and data type interactions
- parameter/localparam forms with expressions and ranges
- identifier references wrapped through multiple expression/reference nodes

## Observation reminders

- grouped declarators are common and should not be collapsed into one symbol
- bit/range expressions often appear as nested binary trees and must stay source-faithful
- keywords, punctuation, and operators may appear as raw token tags rather than category tags
- wrapper chains around identifiers are often longer than around literals

## Useful stimulus axes

- one name versus multiple names under a shared declaration head
- plain range versus parameterized range expressions
- packed-only, unpacked-only, and mixed dimension placement
- typed ports, net ports, var ports, signed ports
