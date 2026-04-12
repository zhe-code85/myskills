// Example Verilog/SystemVerilog filelist.
// Prefer repo-relative paths when the existing build flow uses them.

rtl/example_block.v
tb/example_tb.v

// Include directories and defines usually belong on the command line:
//   scripts/verilog_flow.sh sim --tb example_tb --filelist sim.f --incdir rtl/include --define SIM=1
