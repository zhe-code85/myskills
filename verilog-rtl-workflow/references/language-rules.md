# Language Rules

## Selection policy

- If the user explicitly asks for `Verilog`, use Verilog-compatible syntax only
- If the user explicitly asks for `SystemVerilog`, SystemVerilog syntax is allowed
- If the user does not specify, default to plain Verilog and state that assumption in Stage 1

## Verilog mode

Avoid SystemVerilog-only constructs such as:

- `logic`
- `always_ff`
- `always_comb`
- `typedef`
- `enum`
- packed structs/unions
- `string`

Prefer:

- `reg` and `wire`
- `always @(*)` or `always @*` for combinational logic — both are equivalent in Verilog-2001 and later; do not hand-maintain sensitivity lists for combinational blocks
- Clocked `always @(posedge clk or negedge rst_n)` for sequential logic — always use an explicit edge list for sequential blocks, never `*`
- plain parameters and localparams
- Packed `reg` vectors instead of `string` in TB code when a text-like token such as a wave path is required
- See [verilog-rtl-template.v](./verilog-rtl-template.v) and [verilog-testbench-template.v](./verilog-testbench-template.v) for plain Verilog starting points

Keep synthesizable RTL free of:

- `initial` blocks for design state initialization unless the target flow explicitly supports them
- `#` delays, file I/O, or simulator-only debug code in design logic
- Ad hoc generated clocks or unsafe clock gating when an enable-based structure is possible

## SystemVerilog mode

Allowed when tool-compatible and useful:

- `logic`
- `always_ff`
- `always_comb`
- enums and typedefs
- stronger TB typing when supported by the simulator
- `string`, `automatic` tasks, and assertion-style helpers in TB code

## TB alignment

- By default, TB language should match the RTL language
- Mixed-language style is allowed only when the user explicitly asks for it
- If the repository already standardizes on one TB language, follow the repository unless the user directs otherwise
