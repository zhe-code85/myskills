# Architecture Plan Checklist

Use this reference after the requirement has been converted into a structured contract and before any RTL is written.

## Minimum architecture output

- One-sentence description of the block purpose
- Reuse versus new logic boundary
- Why the design is combinational, sequential, pipelined, or mostly wrapper logic
- List of main internal registers or state variables
- List of reused CBB instances, wrappers, or macros
- List of main combinational decisions or datapath transforms
- Reset behavior
- Latency/throughput summary
- Timing strategy and likely critical path
- CDC strategy for each crossing

## FSM-oriented blocks

- Enumerate each state
- State entry condition
- State exit condition
- Outputs or control actions associated with each state
- Priority rules when multiple transitions are possible

## Datapath-oriented blocks

- Input capture point
- Arithmetic or logical transforms
- Output register point, if any
- Overflow/underflow/sign-extension policy
- Pipeline stage intent when latency is more than one cycle
- Which stage is likely timing-critical and why

## Interface-oriented blocks

- Handshake type: valid/ready, request/ack, start/done, or custom
- Backpressure behavior
- Idle behavior
- Illegal input handling
- Simultaneous event priority
- Where CDC boundaries or reset-domain boundaries sit at the interface

## Consistency checks before RTL

- Every user-visible output is accounted for in the plan
- Every corner case from the requirement has a stated behavior
- Timing assumptions are explicit
- Reset behavior is unambiguous
- Existing CBBs were considered before inventing new logic
- Every CDC path has an explicit safe-crossing mechanism
- Verification targets can be mapped to concrete TB scenarios
