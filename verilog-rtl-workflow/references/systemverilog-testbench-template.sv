`timescale 1ns/1ps

module example_tb;
  localparam int WIDTH = 8;

  logic clk;
  logic rst_n;
  logic in_valid;
  logic [WIDTH-1:0] in_data;
  logic out_valid;
  logic [WIDTH-1:0] out_data;
  string wave_path;

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

  task automatic expect_eq(
    input logic [WIDTH-1:0] actual,
    input logic [WIDTH-1:0] expected,
    input string msg
  );
    if (actual !== expected) begin
      $error("%s actual=%0h expected=%0h", msg, actual, expected);
      $finish(1);
    end
  endtask

  initial begin
    rst_n = 1'b0;
    in_valid = 1'b0;
    in_data = '0;

    repeat (3) @(posedge clk);
    rst_n = 1'b1;

    @(negedge clk);
    in_valid <= 1'b1;
    in_data <= 8'h12;

    @(posedge clk);
    @(negedge clk);
    in_valid <= 1'b0;
    in_data <= '0;

    wait (out_valid === 1'b1);
    expect_eq(out_data, 8'h12, "single transfer");

    repeat (2) @(posedge clk);
    $display("TB PASS");
    $finish;
  end
endmodule
