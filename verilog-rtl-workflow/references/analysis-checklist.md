# Analysis Checklist

Use this checklist before RTL coding. If the user asks for only one stage, fill in the smallest subset needed to avoid blind editing.

## Interface contract

- What language did the user request: Verilog or SystemVerilog?
- What are the exact inputs, outputs, parameters, and widths?
- Which signals belong to which clock domain?
- Is reset synchronous or asynchronous? Active high or active low? How is reset deasserted in each domain?
- Are there enable, valid/ready, request/ack, or start/done semantics?
- Which outputs are combinational versus registered?

## Functional behavior

- What must happen after reset?
- What is the default or idle state?
- Are operations single-cycle, multi-cycle, or pipelined?
- Are simultaneous requests legal? If yes, what is the priority?
- What should happen on overflow, underflow, wrap, saturation, or illegal input?

## Timing, performance, and state

- What is the target clock frequency or clock period?
- What is the expected latency from input acceptance to output visibility?
- Can the block accept back-to-back transactions?
- Are stalls or backpressure possible?
- Is there any requirement for glitch-free outputs?
- Are there state transition restrictions?
- Which paths are likely timing-critical, and will they need pipelining or registered outputs?

## CDC and reset-domain crossings

- Does any signal cross between clock domains or reset domains?
- Is each crossing single-bit level, single-cycle pulse, multi-bit bus, counter, or stream data?
- Which CDC primitive is appropriate: two-flop synchronizer, pulse synchronizer, handshake, async FIFO, Gray-code pointer, or an existing repo CBB?
- Are there status signals that must return across the boundary?
- Is any multi-bit value being sampled without a protocol? If so, redesign it.

## Codebase fit and CBB reuse

- Does the repository already constrain file extensions or language version?
- Does the repository already define naming, reset, or FSM conventions?
- Are there nearby modules that imply protocol behavior not written in the prompt?
- Are there existing TB utilities or compile scripts to reuse?
- Are there existing synchronizers, FIFOs, arbiters, RAM wrappers, skid buffers, or protocol adapters that should be reused?
- Are there existing filelists, constraints, or synthesis scripts that reveal integration requirements?

## Verification targets

Minimum cases to cover:

- Reset behavior
- One nominal operation
- Boundary condition at each width or counter limit
- One negative or illegal case if behavior is defined
- Consecutive operations without idle gap
- CDC-specific cases or backpressure cases when the block requires them
