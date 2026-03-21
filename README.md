# myskills

个人技能仓库，用来持续沉淀、整理和迭代我自己的 Codex/Agent skills。  
A personal skills repository for collecting, refining, and evolving my own Codex/Agent skills over time.

## Overview / 仓库简介

`myskills` 用于管理我自己的技能资产，包括技能定义、参考资料、代理配置，以及后续会逐步补充的文档与规范。当前仓库中的第一个已提交技能是 `super-spec`。  
`myskills` is where I manage my own reusable skills, including skill definitions, references, agent configs, and supporting docs that will grow over time. The first committed skill in this repository is `super-spec`.

这个仓库既服务于我自己的长期维护，也希望让其他人可以快速理解每个技能的定位与结构。  
This repository is meant both for my own long-term maintenance and for helping others quickly understand the purpose and structure of each skill.

## Goals / 仓库目标

- 沉淀可复用的个人技能与工作流
- 为每个技能保留清晰的入口和上下文
- 保持仓库结构简单，方便后续持续新增技能
- 兼顾自用维护与对外阅读体验

- Build a reusable library of personal skills and workflows
- Keep a clear entry point and context for each skill
- Preserve a simple structure that scales as more skills are added
- Balance personal maintenance with external readability

## Getting Started / 开始使用

如果你只是想快速浏览这个仓库，建议按下面的顺序查看：  
If you want a quick way to explore the repository, start in this order:

1. 阅读根目录 `README.md`，了解仓库整体定位  
2. 进入目标技能目录  
3. 打开对应的 `SKILL.md`，查看技能说明、工作流和引用资料  

1. Read the root `README.md` to understand the repository  
2. Open the target skill directory  
3. Read its `SKILL.md` for workflow details, usage rules, and references  

如果你希望把这里的技能复用到自己的环境中，最简单的方式是保留目录结构，并从各技能的 `SKILL.md` 作为入口开始集成。  
If you want to reuse skills from this repository in your own environment, the simplest approach is to preserve the directory structure and integrate each skill starting from its `SKILL.md`.

## Skills / 技能列表

| Skill | Status | Description | Path |
| --- | --- | --- | --- |
| `super-spec` | Active | Spec-driven delivery workflow that connects requirement clarification, planning, OpenSpec artifacts, implementation discipline, and archive closure. | `super-spec/` |

后续新增技能时，直接在这里补充新的一行即可。  
As new skills are added, they can be listed here by appending one new row per skill.

## Repository Structure / 仓库结构

```text
myskills/
├─ README.md
├─ docs/
│  └─ plans/
└─ super-spec/
   ├─ SKILL.md
   ├─ agents/
   └─ references/
```

当前结构采用“根 README 做仓库级导航，技能目录承载具体说明”的方式，便于后续按相同模式继续扩展。  
The current structure follows a simple rule: the root README provides repository-level navigation, while each skill directory contains the detailed skill definition and related assets.

未来新增技能时，建议沿用同样模式：  
As the repository grows, new skills should follow the same pattern:

- 为每个技能创建独立目录
- 在目录中保留 `SKILL.md` 作为主入口
- 将参考资料、脚本、代理配置等内容放入技能目录内部
- 在根 README 的技能列表中补充索引

- Create one directory per skill
- Keep `SKILL.md` as the primary entry point
- Store references, scripts, and agent configs inside that skill directory
- Add the new skill to the root README table

## Roadmap / 后续计划

- 持续补充新的个人技能
- 完善每个技能的说明、示例和参考资料
- 逐步形成更稳定的技能组织方式

- Add more personal skills over time
- Improve the documentation, examples, and references for each skill
- Gradually evolve a more stable structure for the repository
