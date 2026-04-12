`timescale 1ns/1ps

// Parameters: add new parameters here for configurable widths, depths, and
// thresholds. Pass them through when instantiating this module in a TB or
// integration wrapper.
module example_block #(
  parameter WIDTH = 8
) (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  input wire [WIDTH-1:0] in_data,
  output reg out_valid,
  output reg [WIDTH-1:0] out_data
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      out_data <= {WIDTH{1'b0}};
    end else begin
      out_valid <= 1'b0;

      if (in_valid) begin
        out_valid <= 1'b1;
        out_data <= in_data;
      end
    end
  end

endmodule
