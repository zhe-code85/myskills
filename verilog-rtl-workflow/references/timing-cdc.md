# Timing and CDC Guidance

## Timing stance

- Use repository constraints, documented target frequency, or interface timing requirements whenever they exist
- Do not claim timing closure from inspection alone; without synthesis and STA, provide a reasoned timing risk assessment instead of a signoff statement
- Identify the likely longest combinational path before writing RTL
- If target frequency is aggressive, prefer pipelining, registered outputs, or a reused high-speed CBB instead of hoping the path is short enough
- Keep control logic simple on high-fanout paths; decode once, register when appropriate, and avoid deep priority chains when a staged structure is cleaner
- Treat wide arithmetic, large mux trees, compare chains, and cross-module combinational control as timing-risk hotspots

## CDC stance

- Inventory every clock-domain crossing and reset-domain crossing explicitly
- Reuse an existing repository CDC primitive before writing a new synchronizer
- Single-bit level signals: use a standard two-flop synchronizer or the repo-standard equivalent
- Single-cycle pulses or event strobes: use a pulse synchronizer, toggle synchronizer, or handshake, not a raw two-flop sample
- Multi-bit buses: use a handshake, enable-qualified capture, or async FIFO; do not independently synchronize each bit and call it safe
- Async FIFO pointers and counters that cross domains should use a proven scheme such as Gray coding when applicable
- Reset-domain crossings need the same discipline as data CDC; async assert and synchronized deassert is often the safe default, but follow repo convention

## Reporting expectations

- State which timing assumptions were checked with tools versus inferred from structure
- State which CDC paths are covered by an existing proven primitive versus newly written logic
- If a required CDC primitive or timing constraint is missing from the repository, call that out as a risk instead of silently improvising
