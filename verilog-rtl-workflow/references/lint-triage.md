# Lint Triage

Use this reference to keep Stage 4 decisions consistent.

## Must-fix before proceeding

- Syntax or elaboration failures
- Width, sign, truncation, or extension mismatches that can change behavior
- Undriven nets, outputs, or state that affect functionality
- Multiply-driven signals unless the structure is deliberate and tool-clean
- Accidental latch inference
- Combinational loops
- Unsafe clock or reset handling, including ad hoc clock generation or suspicious clock gating
- CDC-unsafe structures such as sampling a multi-bit bus without a protocol

## Review carefully before deferring

- Unused signals, parameters, or states
- Intentionally incomplete `case` or `if` structures that still synthesize safely because the default behavior is explicit
- Tool-specific style warnings that do not affect correctness but might signal a misunderstanding

## Usually safe to defer if documented

- Pure naming or formatting style nits
- Unused debug hooks or reserved fields that are explicitly intentional
- Warning classes the repository convention already accepts, if the current design matches that convention
