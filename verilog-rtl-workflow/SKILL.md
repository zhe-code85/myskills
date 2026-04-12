---
name: verilog-rtl-workflow
description: "Design or refine synthesizable Verilog/SystemVerilog RTL from natural-language hardware requirements or existing module context. Use for module-level digital design tasks such as timing-aware microarchitecture, clock/reset planning, CDC-safe interfaces, CBB reuse, lint, testbench authoring, simulation, and partial-flow work such as RTL-only, TB-only, debug, or CDC review."
---

# Verilog RTL Workflow

Use this skill to work like a senior digital design engineer: inspect the codebase first, prefer proven building blocks, implement synthesizable RTL, and report timing and CDC risk honestly.

## Default behavior

- Scan the repository for existing interfaces, CBBs, constraints, filelists, and verification utilities before inventing new structures
- Reuse existing CBBs, CDC primitives, memories, FIFOs, arbiters, wrappers, and adapters before writing new RTL
- Match the user-specified language exactly; if unspecified, default to plain Verilog and state that assumption
- Keep RTL synthesizable and maintainable; avoid simulation-only constructs in design code unless they are explicitly gated and documented
- Treat timing intent, reset behavior, and CDC safety as part of the design contract, not cleanup after simulation
- Prefer `scripts/verilog_flow.sh` when its lint or simulation modes fit the task; default wave dump path is `build/<tb_module>.vcd`
- Do not claim timing closure or CDC signoff without tool evidence; if synthesis, STA, or CDC tools are unavailable, give a reasoned engineering assessment and call out residual risk
- After two or three unsuccessful fix-and-resim iterations on the same issue, stop thrashing and report the blocker, likely root cause, and needed artifact or decision

## Collaboration

- If the environment and collaboration policy allow subagents, prefer one bounded execution subagent for implementation or verification while the main agent owns assumptions, architecture judgment, and the final user-facing conclusion
- If delegation is unavailable or disallowed, continue locally with the same stage discipline

## Flow selection

- Use the full staged flow for a new module or major redesign
- For RTL-only, TB-only, lint or simulation debug, or CDC or timing review, compress the earlier stages instead of skipping them

## Read on demand

- Contract and planning: [analysis checklist](./references/analysis-checklist.md), [contract template](./references/stage-1-contract-template.md), [architecture plan](./references/architecture-plan.md), [architecture template](./references/stage-2-architecture-template.md)
- Language and templates: [language rules](./references/language-rules.md), [Verilog RTL template](./references/verilog-rtl-template.v), [Verilog TB template](./references/verilog-testbench-template.v), [SystemVerilog RTL template](./references/systemverilog-rtl-template.sv), [SystemVerilog TB template](./references/systemverilog-testbench-template.sv)
- Timing, CDC, and reuse: [timing and CDC guidance](./references/timing-cdc.md), [CBB reuse guidance](./references/cbb-reuse.md)
- Verification: [lint triage](./references/lint-triage.md), [simulation conventions](./references/simulation-conventions.md), [testbench patterns](./references/testbench-patterns.md), [filelist template](./references/filelist-template.f)
- Helper script: `scripts/verilog_flow.sh`

## Stage flow

### Stage 0. Context and reuse scan

Inspect the repository before committing to a new microarchitecture. If the repo is effectively empty or the request is a simple standalone combinational block, say so briefly and proceed.

Required output:

- Reusable modules, wrappers, or CBBs
- Existing language, reset, naming, filelist, and verification conventions
- Available constraints, clocks, or target-frequency information
- Missing information that materially affects correctness, timing, or CDC handling

Exit condition:

- It is clear whether the work should reuse an existing block, wrap one, or introduce new RTL

### Stage 1. Structured design contract

Convert the request into a reviewable engineering contract before coding.

Required output:

- Functional summary and interface summary, including widths and parameters
- Clock and reset domains, CDC boundaries, and selected language
- Timing intent, including frequency, latency, throughput, and backpressure when known
- Assumptions, corner cases, priority rules, and verification targets
- Planned CBB reuse versus new logic boundary

Exit condition:

- Module boundary, reset behavior, timing intent, CDC ownership, corner cases, and language choice are explicit enough to review

### Stage 2. Architecture plan

Produce a compact implementation plan before writing RTL.

Required output:

- Block type, main datapath and control structure, and FSM state list when needed
- Reused CBB instances or wrappers
- Timing strategy, including likely critical paths and pipeline or register placement
- CDC strategy for each crossing and reset or idle behavior
- Rationale for non-obvious choices

Exit condition:

- Every user-visible behavior from Stage 1 maps to a concrete implementation strategy, including timing-sensitive paths and CDC handling

### Stage 3. RTL

Implement synthesizable RTL that matches the plan.

Required output:

- Final RTL source
- File naming and syntax aligned with the selected language
- Reused or wrapped CBBs integrated according to repo conventions

Exit condition:

- RTL is synthesizable, free of exploratory placeholders, and structurally consistent with the timing and CDC plan

### Stage 4. Lint and structural review

Run lint before expanding TB effort and triage findings with engineering judgment.

Required output:

- Exact lint command
- Findings summary grouped by severity
- Fixes applied and any deferred warning with justification

Exit condition:

- No unresolved must-fix findings remain in categories such as syntax or elaboration failure, width or sign mismatch, undriven or multiply-driven logic, accidental latch inference, combinational loops, unsafe clock or reset handling, or CDC-unsafe structure

If lint is unavailable, state the missing tool or environment limit explicitly and continue only if the user still wants the reduced-validation path.

### Stage 5. Testbench

Write a self-checking TB tied to the Stage 1 verification targets.

Required output:

- TB source
- Stable stimulus and checking strategy
- Default wave dump to `build/<tb_module>.vcd`
- CDC-specific or latency-specific checks when needed

Exit condition:

- TB covers reset, nominal path, boundary cases, defined corner cases, and required back-to-back or handshake behavior

If the design includes CDC, document what is and is not realistically validated at RTL simulation level.

### Stage 6. Simulation and engineering summary

Run behavioral simulation and summarize the engineering result.

Required output:

- Exact simulation command, pass or fail result, and waveform path
- Timing assessment
- CDC assessment
- Reused CBB summary
- Remaining risk, if any

Exit condition:

- Targeted scenarios pass, or the remaining blocker is explicitly identified
- The final report distinguishes verified behavior from inferred timing or CDC confidence

## Final delivery

Unless the user asks otherwise, include:

- Requirement summary and architecture summary
- RTL and TB
- Lint command or result and simulation command or result
- Timing assessment, CDC assessment, reused CBBs or reason for new logic, waveform path, assumptions, and remaining risk
