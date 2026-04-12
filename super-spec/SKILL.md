---
name: super-spec
description: Use when a multi-step feature, bugfix, or subsystem needs staged Superpowers delivery plus OpenSpec change tracking. Not for exploration-only, review-only, debug-only, or tiny edits.
---

# Super-Spec

Use this skill to keep the split clean:
- Superpowers drives one delivery point end to end.
- OpenSpec tracks the surrounding requirement line.

## Split

- Superpowers owns clarification, approved design, implementation planning, execution, verification, and branch finishing.
- OpenSpec owns change identity, proposal/design/spec history, milestone status, and archival.
- `docs/superpowers/plans/...` is the only detailed execution plan.
- `openspec/changes/<change>/tasks.md` is milestone-only.
- After sync, durable design lives in `openspec/changes/<change>/design.md`; the brainstorming doc stays a working document.

## Flow

### 1. Explore Or Deliver

- Use `openspec-explore` while the problem is still being shaped.
- Once the user commits to delivery, switch to Superpowers.

### 2. Delivery Path

- Run `brainstorming` for requirements to approved design.
- Preserve the native `brainstorming` handoff.
- After design approval, ensure a dedicated workspace via `using-git-worktrees`. Reuse an existing worktree if one already exists.
- Run `writing-plans` in that worktree.
- Implement through `subagent-driven-development` or `executing-plans`.
- Use `verification-before-completion` before any completion claim.
- Use `finishing-a-development-branch` for branch handling.
- Do not use `openspec-apply-change` as the default implementation path unless the user explicitly wants OpenSpec task-loop execution.

### 3. OpenSpec Path

- Wait until the requirement snapshot and design are approved before creating or refreshing formal OpenSpec artifacts.
- Before creating a change, inspect `openspec list --json`.
- Reuse one clear matching active change. If several active changes plausibly match, ask the user. Never guess.
- Prefer `openspec new change <name>`.
- Treat `openspec-propose` as opt-in bootstrap only. If used, treat its outputs as drafts and reconcile them immediately to the approved requirement, approved design, and milestone-only `tasks.md`.
- On the first sync after design approval:
  - ensure the change exists
  - update `proposal.md` from approved scope
  - update `design.md` from the approved design summary
  - create or update spec deltas when capability contracts changed
  - normalize `tasks.md`
- Later, update OpenSpec only when scope, design, specs, or milestone state changes.

## OpenSpec Artifacts

- `proposal.md`: approved scope, motivation, acceptance boundaries.
- `design.md`: approved design summary and later design deltas.
- `specs/`: requirement contracts only. Add or update delta specs for new externally visible capability, requirement-level behavior changes, API or interface contract changes, acceptance-criteria changes, or user-relevant non-functional changes. Skip internal refactors, tooling changes, test-only work, and other implementation-only changes.
- `tasks.md`: milestone record only. Never mirror `writing-plans`.

```md
# Tasks

- [ ] Requirement snapshot approved
- [ ] Design approved and synced to OpenSpec
- [ ] Implementation plan approved
- [ ] Implementation in progress
- [ ] Verification complete
- [ ] Branch disposition decided
- [ ] Ready to archive
```

- Add extra milestones only if they improve requirement-line traceability.
- Never add fine-grained coding steps, test-by-test steps, or file-level edits.
- A checked box never replaces tests, simulation, lint, review, or other evidence.
- Milestone meaning:
  - `Requirement snapshot approved`: `proposal.md` can be recorded.
  - `Design approved and synced to OpenSpec`: `design.md` is reconciled.
  - `Implementation plan approved`: the `writing-plans` doc exists and has user approval.
  - `Implementation in progress`: execution has started in the dedicated worktree.
  - `Verification complete`: required validation evidence exists and was reviewed.
  - `Branch disposition decided`: merge, PR, keep, or discard is chosen.
  - `Ready to archive`: implementation and verification are complete, the plan copy is stored under the change, and the user wants archival.

## Source Of Truth

- Never maintain competing detailed plans.
- Requirement behavior belongs in OpenSpec specs.
- Implementation detail belongs in the Superpowers design and plan docs.
- `openspec new change` is the preferred container path.
- `openspec-propose` must not overwrite approved Superpowers artifacts.

## Archive

- Treat branch completion and change archival as separate decisions.
- Before archival, copy the final `writing-plans` document to `openspec/changes/<change>/artifacts/implementation-plan.md`.
- Run `openspec-archive-change` only when implementation and verification are complete and the user wants to finalize the requirement line.
- Do not archive while work is still active, the branch is intentionally staying open, or only a PR exists.

## Greenfield Project

When the user is starting a brand-new project (no existing repo or only an empty scaffold), insert two pre-steps before the standard Delivery Path:

1. **Global Design**: Run `brainstorming` to complete project positioning, architecture, milestone planning, and spec scoping. Get explicit user approval before proceeding.
2. **Project Initialization**: Create repo/directory structure, initialize framework/CI/test environment, then split into functional modules. Each module enters the standard Delivery Path independently.

After initialization, the normal Delivery Path and OpenSpec Path apply per module.

## Exception Handling

- **Requirement Change mid-delivery**: Pause execution → return to brainstorming → update the approved requirement and design → sync affected OpenSpec artifacts → re-approve the plan before resuming.
- **Execution Blocker**: Stop immediately. Present at least two viable solutions with trade-offs. Wait for the user to decide. Do not guess or silently pick one.
- **Verification Failure**: Return to the execution phase, fix the issue, re-verify. Repeat until all checks pass. Never claim completion without passing evidence.

## Domain Evidence

- Software: tests, builds, lint, integration checks.
- RTL or hardware: simulation, lint, formal checks, testbenches, tool outputs.
- Other domains: repeatable, auditable validation evidence.
