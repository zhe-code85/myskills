---
name: drawio-chip
description: 生成标准 Draw.io (.drawio) 格式的芯片设计可视化图表；支持从零生成与风格迁移两种模式。从零生成：芯片架构图、数字设计状态机图、数据流图、流程图、数字电路时序图等；风格迁移：参考图 + 内容描述/项目 → 按参考图风格生成新图。确保 XML 格式正确，可直接在 Draw.io 中打开编辑。
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

## 使用时机

**从零生成：**
- 用户需要绘制芯片架构图、模块关系图、数据流图
- 用户需要绘制数字设计状态机图、算法流程图、控制流程图
- 用户需要可视化芯片模块、数据通路、控制逻辑、接口关系或状态变化
- 用户需要绘制时序图 / 波形图、信号时序（时钟、数据总线、握手关系等）
- 用户提到「画个图」「生成架构图」「可视化结构」「绘制流程图」等需求

**风格迁移：**
- 用户提供参考图，希望「按这个风格画」「照着这个排版/配色画」

## 通用规范（两种模式共用）

### 1. XML 格式严格性

- ✅ 所有标签必须正确闭合：`<mxCell>` 对应 `</mxCell>`，绝不能写成 `</mCell>`
- ✅ 使用 `vertex="1"` 标记节点，`edge="1"` 标记连线
- ✅ 每个元素必须有唯一 `id`，从 0 开始递增
- ✅ 特殊字符必须转义：`&` → `&amp;`，`<` → `&lt;`，`>` → `&gt;`

### 2. 标准文件结构

```xml
<mxfile host="app.diagrams.net">
  <diagram name="图表名称" id="图表id">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="宽度" pageHeight="高度" background="#F5F5DC">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- 所有图形元素从 id="2" 开始 -->
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

1. 图表说明（2-3 行）
2. 使用指南：Draw.io 打开、导出 PNG/SVG/PDF、图题与导出说明

## 参考资源

- Draw.io：https://app.diagrams.net/
- 官方文档：https://www.drawio.com/doc/
