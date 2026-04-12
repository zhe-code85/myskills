# Stage 1 Contract Template

Use this structure when the user starts from natural language.

## Functional summary

- Purpose:
- High-level behavior:

## Interface

- Module name:
- Inputs:
- Outputs:
- Parameters:

## Clock, reset, and CDC

- Clocking style:
- Reset style:
- Clock domains:
- Reset domains:
- CDC boundaries and ownership:

## Timing and performance

- Target frequency or clock period:
- Latency:
- Throughput/back-to-back behavior:
- Backpressure or stall behavior:
- Likely timing-critical paths:

## Language

- Selected language:
- Reason if defaulted:

## Reuse plan

- Existing CBBs or wrappers to reuse:
- New logic to write:

## Rules and corner cases

- Priority rules:
- Illegal input behavior:
- Overflow/underflow/wrap policy:
- Idle/default behavior:

## Verification targets

- Reset
- Nominal case
- Boundary case
- Corner case(s)
- CDC or backpressure case(s), if applicable
