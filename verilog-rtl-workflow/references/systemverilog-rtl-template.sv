`timescale 1ns/1ps

module example_block #(
  parameter int WIDTH = 8
) (
  input  logic             clk,
  input  logic             rst_n,
  input  logic             in_valid,
  input  logic [WIDTH-1:0] in_data,
  output logic             out_valid,
  output logic [WIDTH-1:0] out_data
);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      out_valid <= 1'b0;
      out_data <= '0;
    end else begin
      out_valid <= 1'b0;
      if (in_valid) begin
        out_valid <= 1'b1;
        out_data <= in_data;
      end
    end
  end

endmodule
