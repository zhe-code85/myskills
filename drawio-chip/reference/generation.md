# 通用从零生成图表

仅用于**非芯片、非 RTL、非数字模块**的普通 Draw.io 图表：流程图、概念关系图、说明性框图、轻量文字整理图。

如果用户的描述里出现模块、接口、路径、时钟域、寄存器/FIFO、FSM、握手、总线事务或内部框图含义，就不要留在这里，改用 `tech-diagram.md`。

## 硬性路由规则

只要用户提到以下任一语义，就不要使用本文件，改用 `tech-diagram.md`：

- 数字模块、RTL、IP 内部方案、module block diagram、microarchitecture
- 数据通路、控制路径、pipeline/stage、register/FIFO/buffer、FSM、MUX、counter、shifter
- valid/ready、req/ack、总线事务、片上接口、状态/异常/中断反馈
- 芯片/SoC/外设控制器的内部设计框图

波形、时序、WaveJSON 仍使用 `timing-diagram.md`。

## 使用时机

- 用户需要通用流程图、说明性概念图、非 RTL 的组件关系图。
- 用户只想把文字步骤整理成可编辑 `.drawio`。
- 图中不需要数字电路微架构、信号网络、寄存器/FIFO、FSM 或接口握手。

## 工作流程

### Step 1：需求分析

1. 确定图表类型：流程图、概念关系图、说明性框图、轻量模块关系图。
2. 提取节点、分组、输入输出、顺序、依赖或判断分支。
3. 若发现 RTL/数字模块语义，立即切换到 `tech-diagram.md`。

### Step 2：设计布局

- 自上而下：控制流程、步骤和判断。
- 自左向右：处理链路、输入到输出。
- 中心发散：概念关系或依赖网络。
- 节点间距至少 20-30px，避免连线穿过文字。

### Step 3：生成 XML

使用主 `SKILL.md` 的标准 `<mxfile>` 结构。节点用 `vertex="1"`，连线用 `edge="1"`，ID 唯一且保持数字字符串，特殊字符转义。连线文字也用独立 text vertex，不写入 edge `value`，不挂在 edge 下；线旁文字默认透明背景，并放在线旁留白处。

### Step 4：输出与校验

创建 `.drawio` 文件或输出完整 XML，运行：

```bash
python <drawio-chip skill directory>/scripts/validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap <file.drawio>
```

验证失败先修复 XML。最终按主 `SKILL.md` 输出模板交付。

## 常见问题

- 误把数字模块画成通用流程图：切回 `tech-diagram.md`。
- XML 标签不匹配：检查 `<mxCell>` 是否正确闭合。
- 节点/连线不显示：检查 `vertex`/`edge`、`parent`、`source`/`target`。
