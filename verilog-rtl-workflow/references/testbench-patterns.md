# Testbench Patterns

Default to a TB language that matches the RTL language. The primary example below is plain Verilog because the skill defaults to Verilog unless the user explicitly requests SystemVerilog.

Waveforms should be dumped by default to `build/<tb_module>.vcd`. Prefer supporting a `+wave_path=<path>` plusarg and falling back to the default build path when the plusarg is absent.

## Minimal self-checking TB skeleton

```verilog
`timescale 1ns/1ps

module example_tb;
  localparam WIDTH = 8;

  reg clk;
  reg rst_n;
  reg in_valid;
  reg [WIDTH-1:0] in_data;
  wire out_valid;
  wire [WIDTH-1:0] out_data;
  reg [8*64-1:0] wave_path;

  example_block #(
    .WIDTH(WIDTH)
  ) dut (
    .clk(clk),
    .rst_n(rst_n),
    .in_valid(in_valid),
    .in_data(in_data),
    .out_valid(out_valid),
    .out_data(out_data)
  );

  initial clk = 1'b0;
  always #5 clk = ~clk;

  initial begin
    wave_path = "build/example_tb.vcd";
    if (!$value$plusargs("wave_path=%s", wave_path)) begin
      wave_path = "build/example_tb.vcd";
    end
    $dumpfile(wave_path);
    $dumpvars(0, example_tb);
  end

  task expect_eq;
    input [WIDTH-1:0] actual;
    input [WIDTH-1:0] expected;
    input [8*32-1:0] msg;
    begin
      if (actual !== expected) begin
        $display("TB FAIL %s actual=%0h expected=%0h", msg, actual, expected);
        $finish(1);
      end
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = {WIDTH{1'b0}};

    repeat (3) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    in_valid = 1'b1;
    in_data = 8'h12;

    @(posedge clk);
    @(negedge clk);
    in_valid = 1'b0;
    in_data = {WIDTH{1'b0}};

    wait (out_valid === 1'b1);
    expect_eq(out_data, 8'h12, "single transfer");

    repeat (2) @(posedge clk);
    $display("TB PASS");
    $finish;
  end
endmodule
```

## Optional SystemVerilog variant

If the user explicitly requests SystemVerilog, reuse the same structure with SV conveniences such as `logic`, `always_ff`, `string`, and `automatic` tasks. Start from [systemverilog-testbench-template.sv](./systemverilog-testbench-template.sv) instead of translating the plain Verilog example ad hoc.

## Recommended TB structure

- One clock generator per synchronous domain unless the test explicitly studies CDC behavior
- Reset sequence at the beginning of simulation
- Stimulus phase separated from checking logic when possible
- Reusable tasks for repeated transactions
- Immediate fail on deterministic mismatch
- Prefer a stable phase convention: drive on `negedge`, sample after the relevant `posedge` has completed
- Treat same-edge drive/check against sequential RTL as suspicious unless the protocol explicitly demands it
- If using nonblocking assignments in the DUT, avoid checking registered outputs in the same simulation region as the capturing edge
- Default wave dump path should live under `build/`, not the source tree root
- For CDC designs, verify protocol sequencing and synchronizer assumptions, but do not claim metastability proof from RTL simulation alone

## Debug habits

- Print cycle counts or timestamps near the first failure
- Dump waves only when text logs are insufficient
- Keep expected-value logic simpler than the DUT
- If latency is configurable, derive the checker from the parameter instead of hardcoding one cycle
- When a nominal test fails unexpectedly, inspect TB event ordering before assuming the RTL is wrong
- Missing `` `timescale `` directives can create noisy or confusing simulator output; add them to both DUT and TB
