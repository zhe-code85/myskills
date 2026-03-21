# Mapping Guide

Use this guide when converting exploration output into OpenSpec artifacts.

## Exploration to proposal
- Need -> problem statement and value
- Context -> affected users or systems
- Recommendation -> chosen change summary
- Scope -> included now vs excluded now

## Exploration to design
- Recommendation -> core design choice
- Options -> only the important rejected tradeoffs
- Risks -> constraints, dependencies, mitigations

## Write-plan to tasks
Compress detailed steps into 3-7 milestones.

Example:
- Add tests for new behavior
- Implement service logic
- Update API or UI integration
- Add regression coverage
- Verify and document

## Source-of-truth rule
Write-plan supports execution.
OpenSpec artifacts govern the change record.

## Environment gate
Run a short dependency check before execution. If the environment is partial or blocked, keep work at the clarification, planning, or spec stage until the blocker is resolved.
