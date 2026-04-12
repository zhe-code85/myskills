# CBB Reuse Guidance

Use this reference during the Stage 0 scan and again before writing new RTL.

## How to discover reusable blocks

Search the repository before inventing new logic. Use these strategies together rather than relying on one:

### Directory patterns

Scan for common CBB locations:

- `ip/`, `lib/`, `common/`, `shared/`, `cbb/`, `rtl/common/`, `rtl/lib/`, `verification/common/`
- Vendor or third-party IP directories: `vendor/`, `third_party/`, `ext/`
- Project-specific block directories that often accumulate reusable modules

### Keyword search

Search for module names and file names that suggest reusable infrastructure:

- CDC: `sync`, `synchronizer`, `cdc`, `2ff`, `two_flop`, `pulse_sync`, `toggle_sync`
- FIFOs and buffers: `fifo`, `skid`, `buffer`, `pipe`, `elastic`
- Arbitration: `arbiter`, `arb`, `round_robin`, `priority_encode`, `mux`
- Memory: `ram`, `rom`, `spram`, `dpram`, `memory`, `mem_wrapper`
- Clock and reset: `pll`, `clk_div`, `rst_sync`, `reset`, `cg` (clock gating)
- Protocols: `axi`, `ahb`, `apb`, `spi`, `uart`, `i2c`, `valid_ready`, `handshake`
- Counters and math: `counter`, `cntr`, `adder`, `acc`, `sat`, `pipeline`

### Interface-based identification

When reading a candidate module, check the port list to classify it:

- Synchronizer: `din` → `dout` across two clock domains, with `clk_a`/`clk_b` or similar
- FIFO: `wr_clk`, `rd_clk`, `wr_en`, `rd_en`, `full`, `empty`, `din`, `dout` with data width parameter
- Arbiter: N × `request`, N × `grant`, possibly `valid`/`ready` handshake ports
- RAM wrapper: `addr`, `wr_en`/`rd_en`, `wr_data`/`rd_data`, `clk`, parameterized depth and width

A module whose ports match a known pattern but whose name is unclear is still a reuse candidate — read a few lines to confirm.

## Reuse-first checklist

- Prefer wrapping or parameterizing an existing verified CBB over cloning its internals into the new module
- Record which existing block is being reused, which parameters matter, and which assumptions must hold at the integration boundary
- Reuse the repository's reset, clock-enable, and interface conventions so the new block looks native to the codebase

## When new RTL is justified

- The existing CBB does not meet the functional contract
- The latency or timing target cannot be met with the existing block and the limitation is explicit
- The integration overhead of adapting the old block would be higher risk than a small new module
- No candidate exists after searching the patterns above

## Integration patterns

Common ways to fit a CBB into a new design:

- **Direct instantiation with parameter pass-through**: the simplest case; match the CBB's parameter list to the new module's requirements
- **Adapter wrapper**: when the CBB interface almost matches but needs signal renaming, width adjustment, or protocol translation
- **Glue logic around a CBB**: when the design needs a small amount of control or datapath logic surrounding a reused core

## Required reporting

- Name the reused CBBs or state clearly that no suitable CBB was found
- Explain why reuse is safe, or why a new implementation was necessary
