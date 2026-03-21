# README Design

**Date:** 2026-03-21
**Topic:** Repository README for `myskills`

## Goal

Create a bilingual root `README.md` for the `myskills` repository that works as both:

- a personal long-term maintenance guide
- a public-facing introduction for others who want to understand or reuse the repository

## Confirmed Context

- `myskills` is a personal skills repository
- `super-spec` is the first committed skill
- more skills will be added over time
- the README should balance self-use and external readability
- the README should be bilingual in Chinese and English
- the first version should include both repository introduction and installation/usage guidance
- the structure must stay easy to extend as new skills are added

## Options Considered

### Option 1: Lightweight expandable root README

Use the root `README.md` as a repository-level entry point with:

- repository overview
- goals
- getting started
- skill index
- repository structure
- roadmap

Skill-specific details remain inside each skill's own `SKILL.md`.

**Pros**
- scalable as the repository grows
- easy to maintain
- keeps the root document readable

**Cons**
- some skill details require opening another file

### Option 2: Monolithic README

Put all repository information and detailed skill instructions into one root file.

**Pros**
- single document
- easy for first-time readers to scan in one place

**Cons**
- quickly becomes large
- harder to maintain as more skills are added

### Option 3: Navigation-only README

Keep the root README very short and move most content into per-skill documents.

**Pros**
- highly modular
- clean long-term structure

**Cons**
- weak first impression for a small repository
- less useful as a standalone overview

## Recommended Approach

Use **Option 1: Lightweight expandable root README**.

This best fits a personal repository that will continue growing. It provides enough structure now while keeping future additions simple.

## Approved Information Architecture

The root `README.md` should contain:

1. Repository title
2. `Overview / 仓库简介`
3. `Goals / 仓库目标`
4. `Getting Started / 开始使用`
5. `Skills / 技能列表`
6. `Repository Structure / 仓库结构`
7. `Roadmap / 后续计划`

## Content Rules

- Write in paired Chinese and English sections rather than duplicating the entire document in two blocks
- Keep the tone concise and engineering-oriented
- Use a Markdown table for the skill index
- Make the skill list easy to extend by adding new rows only
- Keep the root README focused on repository-level guidance
- Leave deep skill behavior details inside each skill's `SKILL.md`

## Expected Outcomes

- new readers can understand the repository quickly
- future skills can be added without restructuring the README
- installation and usage guidance exists from the first version
