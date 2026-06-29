---
name: drawio-chip
description: Use when generating editable Draw.io .drawio diagrams for chip/RTL architecture, module relationships, data/control flow, FSMs, timing waveforms, WaveJSON, bus transactions, or style-matched diagrams from a reference image; triggers include 画芯片架构图、时序图、波形图、状态机图、按参考图风格画.
---

# Draw.io 图表

本 Skill 指导 Agent 生成**标准的 Draw.io 格式图表**（.drawio 文件），主要面向**芯片设计可视化**，支持两种模式：**从零生成**（芯片架构图、数字设计状态机图、数据流图、流程图、数字电路时序图等）与**风格迁移**（参考图 + 内容 → 按参考图风格生成新图）。

## Step 0：任务识别

| 条件 | 执行 |
|------|------|
| 用户提供**参考图**，且希望「按这张图的风格」画新图 | 执行 `reference/style-migration.md` |
| 用户需要绘制时序图 / 数字电路时序图 / 波形图 / 信号波形 / timing diagram / WaveJSON | 执行 `reference/timing-diagram.md` |
| 用户需要绘制芯片架构、状态机、数据流、控制流程、片上接口交互、总线事务等芯片设计技术图 | 执行 `reference/tech-diagram.md` |
| 其他情况（从零生成） | 执行 `reference/generation.md` |

## 交付原则

- 产物必须是可编辑的 `.drawio` 文件或完整 `.drawio` XML；不要只输出图表说明。
- 如果用户没有给出足够内容（节点、关系、信号、项目路径或图表目标），先追问关键缺口。
- 生成后运行 `python3 drawio-chip/scripts/validate_drawio.py <file.drawio>`；若用户只要 XML 文本，用同一脚本从 stdin 校验。
- 最终回复必须包含：图表用途、文件路径或 XML 块、验证结果、Draw.io 打开方式、需要用户确认的假设。

## 通用规范（两种模式共用）

### 1. XML 格式严格性

- ✅ 所有标签必须正确闭合：`<mxCell>` 对应 `</mxCell>`，绝不能写成 `</mCell>`
- ✅ 使用 `vertex="1"` 标记节点，`edge="1"` 标记连线
- ✅ 每个 `<mxCell>` 必须有唯一且稳定的 `id`；可用连续数字或语义化 ID，不要求连续
- ✅ 特殊字符必须转义：`&` → `&amp;`，`<` → `&lt;`，`>` → `&gt;`

### 2. 标准文件结构

```xml
<mxfile host="app.diagrams.net">
  <diagram name="图表名称" id="图表id">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="900" pageHeight="800" background="#F5F5DC">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- 所有图形元素从 id="2" 或语义化 ID 开始 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### 3. 常用样式

- **2D 节点**：`rounded=1;whiteSpace=wrap;html=1;fillColor=#颜色;strokeColor=#333333;strokeWidth=1;fontSize=11`
- **3D 节点（可选立体风格）**：`shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;darkOpacity=0.05;darkOpacity2=0.1;size=20;fillColor=#颜色;strokeColor=#333333;strokeWidth=1.5`
- **连线**：`edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=2;endArrow=classic`
- **虚线连接 / 辅助线**：`dashed=1`

### 4. 输出要求

1. `.drawio` 文件路径或完整 XML 内容
2. 图表说明、核心组件、布局与配色
3. 验证命令与结果；验证失败时先修复 XML，不要交付损坏图
4. 使用指南：Draw.io 打开、导出 PNG/SVG/PDF、图题与导出说明
5. 需要用户确认的假设或后续可调整项

### 5. 标准输出模板

```text
图表用途：...
文件：path/to/file.drawio
验证：python3 drawio-chip/scripts/validate_drawio.py path/to/file.drawio -> OK
说明：...
Draw.io：打开 https://app.diagrams.net/，选择 File > Open From > Device。
假设：...
```

## 参考资源

- Draw.io：https://app.diagrams.net/
- 官方文档：https://www.drawio.com/doc/
