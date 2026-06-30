# 状态机 / 状态迁移图渲染

用于把已有 FSM、状态表、状态转移说明、RTL `case` 状态逻辑，或用户给出的状态迁移草图渲染为可编辑 Draw.io `.drawio` 状态迁移图。输入源头可以是 RTL/SystemVerilog 片段、状态 enum、case/next-state 逻辑、设计规格、表格、文字说明、截图、已有 `.drawio` 或白板草图。

本文件只指导状态机的视觉渲染和 Draw.io XML 生成，不设计状态机、不补状态、不推导缺失迁移。若输入缺少状态、迁移条件、复位入口或关键出口，先追问。

状态机图通常使用白底、黑色细线、圆形状态节点、浅绿色强调旁路状态、实线/虚线区分迁移类型，并用极简图例说明线型和颜色含义。

## 输入检查

在写 XML 前确认以下信息是否足够渲染：

| 输入项 | 用途 | 缺失时处理 |
| --- | --- | --- |
| 状态名 / enum 名 | 决定状态节点 | 追问状态清单或 RTL 状态定义 |
| 初始 / reset 状态 | 决定入口箭头 | 追问 reset 后进入哪个状态 |
| 状态迁移条件 | 决定箭头和条件标签 | 追问缺失条件；不要自行补条件 |
| 自动 / 默认迁移 | 决定是否使用虚线 | 未说明则统一实线，不猜测 |
| 异常 / 完成 / 返回路径 | 决定外圈回边和出口 | 未提供则不添加 |
| 状态类别 | 决定是否少量用色强调 | 未提供则全部白底 |

## 渲染原则

- **先提取已有语义**：只使用输入里已经给出的状态名、转移条件、复位入口、异常/完成返回路径和输出动作。缺状态或缺条件时追问，不补状态。
- **状态节点形状**：状态默认用圆形或接近圆形的 ellipse，不用普通模块框。普通状态白底黑边；特殊/可旁路/关键状态可用低饱和浅绿色填充。状态名居中，使用短名称或 RTL enum 名；长名称换行，不把动作说明塞满圆内。
- **布局骨架**：把初始/空闲状态放在左侧或左上，核心传输/处理状态放在中部，完成/清理/错误路径放在右侧或下方。主迁移按顺时针、左到右或上到下形成可追踪路径；返回/重试/异常迁移走外圈。
- **状态层次**：若存在 bypass、optional path、error path、cleanup path 等类别，用位置和浅色强调表达；不要用大量颜色分类。浅绿色只作为少数状态的视觉强调，不让颜色承担唯一语义。
- **初始/复位入口**：用短箭头或 `reset/start` 标签指向初始状态；不要把 reset 画成普通业务状态。若 reset 条件已给出，标签靠近入口箭头。
- **迁移线型**：条件触发的状态迁移用黑色实线箭头；自动/默认/无条件迁移可用黑色虚线箭头。若输入没有区分自动和条件迁移，不要自行猜测线型语义，统一用实线并在图例或说明中注明。
- **迁移走线**：优先使用平滑弧线或少折点连线，让状态图呈网络/环路结构；回边和异常路径走外侧，避免穿过状态圆。双向迁移拆成两条错开的弧线，不重叠在同一条线上。
- **条件标签**：不要把条件写进 edge `value`；用独立透明 text vertex 放在箭头附近。标签贴近对应箭头但不压线、不覆盖状态，长条件拆成 2-3 行。条件密集时优先移动标签或拉开节点间距，不用白底文字块遮线。
- **条件写法**：保留原始 RTL/规格里的信号名和极性，例如 `tx_valid && ready`、`bit_cnt == 0`、`cs_n deassert`。不要把条件改写成新协议语义。
- **图例**：当使用浅绿色状态、虚线箭头或多种线型时，在左下角或空白角落放一个极简 legend，例如 `green = bypass-capable state`、`solid = conditional transition`、`dashed = automatic transition`。只有一种状态/线型时不强行加图例。
- **拥挤控制**：超过 8-10 个状态时，优先扩大画布、按 phase 分簇或分层；超过 15 个状态时，考虑 overview + detail。迁移密集处先牺牲紧凑度，保证箭头、条件、状态一一对应。

## Draw.io XML 规则

- 使用主 `SKILL.md` 的标准 `<mxfile>` 结构。
- 每个状态是独立 `vertex="1"` 的 ellipse。
- 每条迁移是独立 `edge="1"`，`value` 必须为空或省略。
- 条件标签是独立 text vertex，`parent="1"`，不要挂在 edge 下。
- 每个 `<mxCell>` 使用唯一稳定的数字字符串 `id`；`source`、`target`、`parent` 也引用数字字符串 id。
- 特殊字符必须转义：`&` -> `&amp;`，`<` -> `&lt;`，`>` -> `&gt;`。

## 样式片段

### 普通状态

```xml
<mxCell id="20" value="IDLE" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1" vertex="1" parent="1">
  <mxGeometry x="120" y="120" width="72" height="72" as="geometry"/>
</mxCell>
```

### 浅绿色强调状态

```xml
<mxCell id="21" value="BYPASS" style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#D9EAD3;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1" vertex="1" parent="1">
  <mxGeometry x="260" y="120" width="72" height="72" as="geometry"/>
</mxCell>
```

### 条件迁移和独立条件标签

```xml
<mxCell id="22" value="" style="edgeStyle=elbowEdgeStyle;elbow=horizontal;rounded=1;html=1;strokeColor=#000000;strokeWidth=1;endArrow=classic" edge="1" parent="1" source="20" target="21">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
<mxCell id="23" value="cond" style="text;html=1;align=center;verticalAlign=middle;fontFamily=Consolas;fontSize=10;fontColor=#000000;fillColor=none;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="185" y="100" width="70" height="18" as="geometry"/>
</mxCell>
```

### 自动 / 默认迁移

```xml
<mxCell id="24" value="" style="edgeStyle=elbowEdgeStyle;elbow=horizontal;rounded=1;html=1;strokeColor=#000000;strokeWidth=1;dashed=1;endArrow=classic" edge="1" parent="1" source="21" target="20">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## 质量检查清单

- [ ] 所有状态、迁移、条件均来自输入或用户确认的假设。
- [ ] 没有自行添加状态、异常路径、完成状态或默认迁移。
- [ ] 状态节点为圆形 / ellipse，普通状态白底黑边，少数强调状态使用浅绿色。
- [ ] 实线 / 虚线的含义来自输入或在图例中说明。
- [ ] 所有 edge 的 `value` 为空；条件标签是独立透明 text vertex。
- [ ] 箭头、条件标签和状态节点不互相遮挡；返回/异常路径走外圈。
- [ ] XML 可读且通过 `validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap`。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| 把 FSM 画成普通模块框图 | 改成状态节点 + 状态迁移箭头 |
| 根据目标自行补状态 | 停止生成，追问已有状态或 RTL 状态定义 |
| 把条件写在 edge `value` 上 | 清空 edge `value`，改用独立 text vertex |
| 线型含义靠猜 | 未给出自动/条件区别时统一实线或追问 |
| 大量状态随机上色 | 只用少量浅绿色强调输入中已有的特殊状态类别 |
