# Simulation Conventions

## Default commands

Preferred order:

1. `verilator --lint-only`
2. `iverilog -g2012 -Wall`
3. `vvp`

Helper script:

```bash
# <skill-scripts> is the path to this skill's scripts/ directory.
# File paths (rtl/*.v, tb/*.v, sim.f) are relative to the project repository,
# not to the skill directory.
<skill-scripts>/verilog_flow.sh lint --top <top_module> --files "rtl/a.v rtl/b.v"
<skill-scripts>/verilog_flow.sh sim --tb <tb_module> --files "rtl/top.v tb/top_tb.v"
<skill-scripts>/verilog_flow.sh sim --tb <tb_module> --filelist sim.f --incdir rtl/include --define SIM=1
```

Filelist format: see [filelist-template.f](./filelist-template.f).

## Waveforms

- Default wave dump path is `build/<tb_module>.vcd`
- Prefer TBs that accept `+wave_path=<path>` and fall back to the default build path
- Do not dump waves into the source tree root unless the repository already requires it

## Debug order

When simulation fails:

1. Re-check the Stage 1 contract
2. Re-check TB event ordering and checker correctness
3. Re-check RTL against the Stage 2 plan
4. Re-run lint if RTL changed materially
5. Re-run simulation
6. After two or three failed fix attempts on the same issue, stop and report the blocker instead of continuing to guess

## Common pitfalls

- Same-edge TB drive and DUT sampling races
- Reading registered outputs before NBA updates become visible
- Missing `` `timescale `` directives creating noisy timing diagnostics
- Treating RTL simulation as proof of CDC safety; metastability handling still depends on the chosen crossing primitive
