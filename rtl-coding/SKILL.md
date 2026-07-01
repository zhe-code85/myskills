---
name: rtl-coding
description: "在已有稳定模块设计输入，或用户给出可直接编码的模块规格时使用。用于实现、补齐或修复 Verilog/SystemVerilog 模块 RTL，包括 CBB/IP wrapper、参数适配、lint/静态检查/仿真暴露的实现层问题修复。若任务仍处于需求澄清、架构拆分、模块设计生成或微架构决策未闭合阶段，不要使用本技能，应先要求补齐设计输入。"
---

# RTL 编码技能

## Overview

本技能把稳定模块设计输入落成可综合、可追溯的 RTL。完成标准是 RTL 与 `verification_input` 同步落盘，并在交付前用输入准备度提炼的 `<module_name>_checklist` 与 `coding_standards.md` 共同完成 review。

本技能自包含所有编码入口判据、编码规范入口、反馈格式和目录约定。不要依赖其他 skill 的正文或 reference；需要读取的 reference 都在当前技能的 `references/` 下。

阶段边界：本技能负责模块级 RTL 实现、输入准备度检查、编码完成前 review 和验证交接物；不负责重新定义需求、子系统边界、跨模块协作、架构分块或未闭合的微架构决策。若输入不稳定，按逐项确认方式询问用户，而不是边猜边写。

## Quick Reference

- 稳定模块设计输入 + 写 RTL -> 使用本技能。
- 只有口头方向或功能想法 -> 先要求补齐模块设计输入。
- 发现设计缺口 -> 生成阻塞反馈，建议回到最近的设计阶段。
- 收到实现 bug / lint 风格问题 -> 回到步骤 1，按当前输入修 RTL 与交接物。

## Common Mistakes

- 跳过 `references/coding_readiness_checklist.md` 的输入准备度检查，把不稳定输入当成可编码输入。
- 用编码阶段补齐规格、接口、复位、异常或微架构决策。
- 输入准备度阶段未确认 CBB/IP 复用、自实现或 wrapper/参数适配决定，编码时临时选择实现方案。
- 只交 RTL，不交 `<module_name>/verification_input.md`，或交付前未用输入准备度提炼的 `<module_name>_checklist` 与 `coding_standards.md` 共同 review。
- 把未执行的 lint、仿真或自检写成已通过。
- 在 verification_input 或最终回复中引用当前 RTL 不存在的信号、逻辑块或路径。
- 将一个 `always @(*)` 聚合块同时驱动多个输出或多个 `*_comb`，却把单目标组合块规则标为 `pass`。
- 把行为仿真或 smoke/sanity 通过当成本技能必须完成的 gate；本技能的 gate 是静态一致性、编码规则和交接物一致性。

## Red Flags — STOP

出现以下任一情况，停止改 RTL 或停止交付，按「阻塞、反馈与重入」输出。输入准备度问题优先按 `references/coding_readiness_checklist.md` 判断。

### 规则与实现冲突

- 用户要求违反强制编码规则、接受半成品、以 TODO 或注释掩盖缺口。
- 编码规则、项目 coding style 或强制约束之间存在未解决冲突。

### 规则违反

- 输出端口使用 `wire` 直接组合输出，没有对应的 `reg` 信号和时序更新块。
- 状态机的状态转移（next-state）组合逻辑没有以当前状态寄存器为选择条件使用顶层 `case` 语句组织。

### 证据与交付不一致

- 交付前无法把 RTL、`verification_input` 与输入来源逐项对上。
- review 结论只能口头解释，不能定位到真实 RTL 文件、信号或逻辑块。
- verification_input 或最终回复引用了当前 RTL 不存在的信号、逻辑块或路径。
- 未执行的 lint、仿真、自检或反馈被写成已通过。

## References

按需读取当前技能内 reference：

- `references/coding_readiness_checklist.md`：编码前输入准备度检查表；不齐全时停止，不进入编码。
- `references/coding_standards.md`：默认 RTL 编码规范、强制规则，并与输入准备度提炼的 `<module_name>_checklist` 共同作为编码完成前 review 依据；`<module_name>_checklist` 不单独落文件。

## 执行流程

### 1. 检查输入准备度

- 从用户输入或用户指定文档中提取模块设计输入；若项目已使用 `<module_name>/module.md` 或等效模块文档，优先读取该文件。
- 读取 `references/coding_readiness_checklist.md`，逐项判断输入是否已经稳定到可以编码。
- 若 checklist 存在会影响 RTL 结构、接口、时序、异常、CBB/IP 复用或验证关注点的缺口，停止编码并按「阻塞、反馈与重入」逐项向用户确认；不要一次性抛出完整问题清单，也不要进入下一步。
- 如果当前输入来自用户直达请求，可先把已经明确的稳定规格固化为模块设计输入快照；不得补充新的设计决策。
- 编码假设只能来自用户输入、指定文档、项目模块文档和输入准备度检查结论；不要把上一阶段 stdout、路由摘要或未落盘对话上下文当作稳定输入。
- 输入准备度通过后，从 checklist 的 `pass` 项和约束项提炼本次 `<module_name>_checklist`；它是编码和 review 的工作清单，不创建 `<module_name>_checklist.md`。review 通过后，只在 `review_report.md` 中记录对应结论、证据、偏离项和未执行项。

简单模块也必须先通过输入准备度检查。输入可以来自用户当前输入、用户指定文档或项目模块文档。

### 2. 读取编码规范

- 读取 `references/coding_standards.md`。
- 项目已有明确 coding style 时优先遵循项目规范；若与默认规则不同，在最终回复的 review 结论中说明依据和偏离范围。

### 3. 编码

- 将 RTL 写入 `<module_name>/*.v` 或 `<module_name>/*.sv`，具体写法遵循 `references/coding_standards.md`。
- 分段生成 RTL，不要一口气拼完整文件：
  1. `module` 与 port list：先落模块声明、参数、端口方向、位宽、端口注释和基础信号声明。
  2. 控制路径：再落 FSM、握手、仲裁、使能、状态转移、异常/边界控制和寄存器更新，并为每个主要功能块写明职责。
  3. 数据路径：再落数据选择、运算、buffer、pipeline 数据寄存器和输出数据组合逻辑，并为关键功能块写明输入依赖和输出结果。
  4. 整体收敛：最后补齐输出端口寄存器时序更新块、CBB/IP 例化、输出绑定、默认值、注释和文件级一致性；每个 output 端口必须有对应的 `reg` 信号和时序更新块。
- 每一段完成后，检查该段是否仍服从模块设计输入和输入准备度检查结论；不得把关键结构、延迟、吞吐、顺序、并发或异常语义替换成“功能近似”方案。
- 如果输入准备度检查要求使用 CBB/IP，RTL 必须实际例化或引用指定路径对应的 CBB/IP 模块；不得改为自实现或替换为未确认模块。
- verification_input 和最终回复里引用的信号名、逻辑块、阶段路径与文件路径，必须来自当前真实 RTL 和已落盘文件。
- 若编码过程中命中 `Red Flags — STOP`，不在本阶段自行改规格；整理阻塞反馈。

### 4. 生成验证交接物

- 编码完成后，写入 `<module_name>/verification_input.md`。
- 交接物至少包含：基本功能主路径、边界场景、错误场景、实现敏感点、建议优先级、关联工件。
- 若模块文档定义了关键约束，必须把这些约束转成下游可读取的检查关注点；不要只写宽泛的“功能验证”。
- 将编码中发现的潜在风险或不确定点写入交接物，供后续测试和验证读取。
- 关键设计约束必须能在当前 RTL 中定位；若无法给出代码级依据，不交付下游。
- 可选自检证据只引用本次真实生成且可打开的日志；未执行就留空。

### 5. 编码完成前 review

- 输入侧：`references/coding_readiness_checklist.md` 的输入准备度结论仍有效，当前 RTL 没有反向引入新的设计假设。
- 规范侧：按 `references/coding_standards.md` review 当前 RTL 的编码规范、注释完整性、强制规则和风格偏离。
- 设计侧：按步骤 1 提炼的 `<module_name>_checklist` review 当前 RTL 的接口、复位、异常、pipeline、寄存器语义、CBB/IP 决定和验证关注点。
- 输出侧：RTL 与 `verification_input` 真实落盘并互相一致。
- 一致性侧：verification_input 与最终回复中的关键信号、逻辑块、阶段路径和文件路径，能在当前 RTL 与工作区逐一定位。
- 结论侧：最终回复的 review 结论必须同时覆盖 coding standards 和本次 `<module_name>_checklist`；尤其核对组合逻辑单目标规则。
- 证据侧：只记录真实执行过的 lint、静态检查或附加自检；未执行的反馈不得写成通过，被引用日志路径必须真实存在。
- 报告侧：review 通过后，写入 `<module_name>/review_report.md`，记录 `<module_name>_checklist` 与 `coding_standards.md` 的 review 结论；coding standards 结论必须包含端口注释、功能点注释、功能块注释和关键实现注释的检查结果。

- Review 不通过时，回到步骤 3 修改 RTL，并同步更新 `verification_input.md`；重复步骤 3-5，直到 `<module_name>_checklist` 与 `coding_standards.md` 全部通过后，才写入 `review_report.md` 并交付。

## 输出

- RTL 主输出：`<module_name>/*.v` 或 `<module_name>/*.sv`
- 验证主交接物：`<module_name>/verification_input.md`
- Review 报告：`<module_name>/review_report.md`

## 交接工件契约

- 模块目录：所有交付物默认直接位于 `<module_name>/` 下；若项目已有明确目录约定，优先遵循项目约定，并在最终回复中说明。
- 输入来源：用户输入、用户指定文档或项目模块文档；若需要固化输入，写入 `<module_name>/module.md`。
- RTL 输出：一个或多个 `<module_name>/*.v` / `<module_name>/*.sv`，直接位于模块目录下。
- 验证交接物：`<module_name>/verification_input.md`，描述后续测试/验证必须覆盖的主路径、边界、异常、复位恢复和实现敏感点。
- Review 报告：`<module_name>/review_report.md`，记录 `<module_name>_checklist` 与 `coding_standards.md` 的 review 结论、偏离说明、未执行检查和真实自检证据。
- 下游读取顺序：先读 `verification_input.md`，再读 `review_report.md`，最后读 RTL 源码。
- 更新规则：RTL、输入假设、CBB/IP 路径或关键行为变化后，必须同步更新受影响的 `verification_input.md` 和 `review_report.md` 内容。

## 完整交付与局部修复

- 完整模块交付：必须生成或更新 RTL、`verification_input.md` 和 `review_report.md`。
- 局部 RTL 修复：只更新受影响的 RTL 和交接物章节；未受影响的输入假设、验证关注点和 review 结论可保持不变，但最终回复必须说明影响范围。
- 若局部修复改变接口、复位、时序、异常、寄存器语义、CBB/IP 路径或验证关注点，按完整模块交付重新执行步骤 1-5。

## 阻塞、反馈与重入

先区分“可整改问题”和“阻塞问题”：

- 可整改问题：RTL 实现、风格、lint、静态检查、仿真反馈、`<module_name>_checklist` 或 `coding_standards.md` review 不通过。此类问题留在本技能内整改：从步骤 1 重新确认输入，回到步骤 3 修改 RTL，重复步骤 3-5，直到 review 全部通过。
- 阻塞问题：输入准备度不通过，或缺少会影响接口、复位、异常、pipeline、寄存器语义、CBB/IP 路径、关键行为或验证关注点的信息。此类问题停止编码，按优先级逐项向用户确认，不要一次性抛出完整问题清单；不要调用或依赖其他 skill。

阻塞反馈采用逐项确认方式。每轮只询问一个最关键阻塞项，优先级为：接口形态与端口 -> 时钟复位 -> CBB/IP 或缓冲结构 -> 状态机/异常恢复 -> 寄存器语义 -> 验证关注点。当前环境提供 `AskUserQuestion` 或等价交互式澄清工具时，必须用该工具提出本轮 `question`；没有交互式澄清工具时，才使用文本阻塞反馈格式。用户回答后，回到步骤 1 重新检查输入准备度；仍有阻塞时再问下一项。

每轮阻塞反馈必须包含 7 个字段：

- `current_stage`: `rtl-coding`
- `blocked_step`: 当前阻塞步骤，如 `input-readiness` / `coding` / `verification-handoff` / `final-review`
- `problem_class`: `spec` / `interface` / `architecture` / `requirement` / `tooling` / `conflict`
- `blocking_item`: 本轮只处理的一个最关键阻塞项
- `known_context`: 已确认且与本轮问题相关的上下文，避免用户重复说明
- `question`: 向用户提出的一个具体问题；需要选择时给出少量明确选项，并推荐默认项
- `reentry_step`: 用户回答后从本技能哪个步骤重入

本技能特有规则：

- 输入准备度不通过时，不写 RTL；补齐输入后从步骤 1 重入。
- 编码过程中暴露新的规格缺口或结构性冲突时，不把问题埋在注释里继续推进，按逐项确认方式询问用户。
- 用户指令与 `coding_standards.md` 强制规则冲突时，不用“用户指令优先”作为放行理由；停止编码并按逐项确认方式询问用户。
- 用户要求接受半成品交付时，不把该请求翻译成“先做主通路”；说明当前交付不允许，并按逐项确认方式询问最关键缺失项。
- 代码修复、lint 修复或仿真反馈修复后，从步骤 1 重新确认输入；按「完整交付与局部修复」更新受影响的 RTL、`verification_input.md` 和 `review_report.md` 后再交付。
