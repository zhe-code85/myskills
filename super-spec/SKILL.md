---
name: super-spec
description: adapt vague or clear software and product requirements into a concise delivery flow that starts with superpowers-style exploration and write-plan, passes through a mandatory spec review loop, maps the approved result into openspec change artifacts, drives implementation with tdd, worktree isolation, incremental code review, and finish-gate verification, then archives completed changes back into living specs without duplicating validation across stages. use when a request is ambiguous, under-specified, or already defined but still needs structured planning, execution guidance, and spec-first closure.
---

# Super-spec

## Overview

Use this skill to turn a vague or clear requirement into a spec-driven delivery flow with strict stage boundaries. Keep it lean: clarify only what matters, approve one design, map it into OpenSpec artifacts, implement with Superpowers-style discipline, then archive the finished change.

## Workflow

Follow this sequence:

0. Check environment readiness.
1. Classify the request as vague or clear.
2. Run concise Superpowers-style exploration.
3. Write one compact plan.
4. Run a mandatory spec review loop.
5. Create or update OpenSpec change artifacts.
6. If implementation is requested, isolate work, implement with TDD, and request incremental review.
7. Finish the development branch.
8. Archive the completed change into living specs.

## Hard boundary rules

Use one primary gate per concern. Do not repeat the same validation in multiple stages.

- **Design quality** is checked only in the spec review loop.
- **Environment readiness** is checked only in startup and worktree setup.
- **Task correctness** is checked with TDD for the current step.
- **Incremental code quality** is checked with code review between task groups.
- **Release readiness** is checked only in the finish gate.
- **Specification truth** is maintained only in OpenSpec artifacts and archive.

OpenSpec must not repeat design review, environment checks, task-level testing, or final delivery verification that Superpowers stages already covered.

## 0) Startup environment check

Before planning or implementation, verify:
- required runtime and package manager
- repository access and project root
- test or verification command availability
- OpenSpec CLI or `openspec/` structure readiness
- git branch or worktree support when isolation is useful

Classify the result as:
- **ready**: planning and implementation can proceed
- **partial**: planning can proceed but execution has blockers
- **blocked**: stop before implementation and report missing dependencies

If the result is partial or blocked, continue only with clarification, exploration, planning, and artifact drafting.

## 1) Intake and classification

Treat the input as **vague** when users, goals, constraints, scope, success criteria, or non-goals are missing.
Treat the input as **clear** when feature behavior and boundaries are already defined.

For vague requests, tighten these fields before planning:
- user or actor
- problem or desired outcome
- context or trigger
- constraints
- success criteria
- non-goals

For clear requests, confirm the same fields briefly and continue.

## 2) Superpowers-style exploration

Use concise structured expansion, not open-ended brainstorming.

Produce:
- **Need**
- **Context**
- **Options**: only when ambiguity materially affects design or scope
- **Recommendation**: one chosen path with brief tradeoffs
- **Scope**: MVP, later, non-goals
- **Risks**

Stay compact. Prefer one recommended path.

## 3) Write-plan

Create one compact execution plan before implementation.

The plan must:
- break work into small verifiable steps
- group steps by outcome
- note expected validation for each step
- highlight dependencies and ordering
- stay shorter than the full spec set

Default shape:
1. Setup or prerequisite checks
2. First failing test or validation target
3. Minimal implementation step
4. Re-run tests and refine
5. Repeat for the next capability
6. Final verification and cleanup

Treat the write-plan as an execution aid, not the final source of truth.

## 4) Mandatory spec review loop

After exploration and write-plan, run one explicit design review pass before artifact generation or implementation.

Review for:
- requirement completeness
- scope discipline and non-goals
- architectural fit
- avoidable complexity
- testability and validation path
- major unanswered risks

If the review finds significant issues, revise the recommendation or plan and review again. Do not move forward until the design is approved.

## 5) OpenSpec artifact generation

After approval, create or update OpenSpec change artifacts. Prefer the current propose-style flow when available. Otherwise maintain the same artifact set manually.

Use OpenSpec roles like this:
- `openspec/changes/<change-name>/proposal.md`
- `openspec/changes/<change-name>/design.md`
- `openspec/changes/<change-name>/tasks.md`
- `openspec/changes/<change-name>/specs/...`

Mapping rules:
- **proposal**: why this change exists and what changes now
- **design**: only the approved approach, constraints, and tradeoffs
- **specs**: behavioral, testable requirements
- **tasks**: higher-level milestones derived from the write-plan

Do not copy detailed execution steps into specs. Preserve only the selected path and notable rejected tradeoffs.

## 6) Isolated implementation

If implementation is requested and the environment is ready, isolate the work before coding.

Preferred order:
1. create or switch to a dedicated branch or worktree
2. confirm setup succeeds and baseline checks pass
3. implement by following the approved write-plan

Use TDD when practical:
1. write or identify a failing test
2. implement the smallest change that should pass
3. run validation
4. refactor safely
5. continue to the next step

## 7) Incremental code review

Request code review between meaningful task groups, not after every tiny edit.

Use review to check:
- alignment with approved design and tasks
- code quality and maintainability
- missing tests or broken assumptions
- scope drift

Use review to assess the new increment. Do not rerun full design review here.

## 8) Finish gate

Before merge or handoff, run one final finish pass.

Confirm:
- the approved change is implemented
- required tests or verification pass
- the branch or worktree is ready to merge, preserve, or discard
- summary and artifact status are up to date

This is the only final delivery gate. Do not duplicate it in archive.

## 9) Archive and closure

After the finish gate passes:
- archive the completed change into `openspec/specs/`
- remove or close obsolete change-specific scaffolding if the workflow requires it
- summarize what changed and what remains out of scope

OpenSpec is the final source of truth for completed changes.
The write-plan is temporary and execution-oriented.

## Output defaults

Keep output lean.

### For vague requests
Return:
1. clarified requirement
2. options and recommendation
3. write-plan
4. review outcome
5. OpenSpec change artifacts

### For clear requests
Return:
1. confirmed requirement
2. short write-plan
3. review outcome
4. OpenSpec change artifacts

### For implementation follow-up
Return:
1. current task group
2. failing test or validation target
3. next minimal code step
4. review or verification result
5. finish-gate or archive readiness
