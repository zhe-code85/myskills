# 通用从零生成图表

在无参考图、且任务没有命中 `tech-diagram.md` 或 `timing-diagram.md` 的情况下，从零生成通用 `.drawio` 图表。芯片架构、RTL 状态机、数据流、控制流、总线事务等专项技术图优先使用 `tech-diagram.md`；波形和信号时序优先使用 `timing-diagram.md`。

## 使用时机

- 用户需要通用流程图、说明性框图、概念关系图、轻量模块关系图
- 用户提到「画个图」「可视化结构」「绘制流程图」，但没有明确芯片专项语义
- 用户需要简单整理文字内容为 `.drawio`，且不涉及波形、RTL 状态机、总线事务或片上接口

## 工作流程

### Step 1：需求分析

1. **确定图表类型**：
   - 通用流程图（步骤、判断、分支、结束）
   - 说明性框图（概念、组件、依赖、边界）
   - 轻量模块关系图（模块、输入输出、依赖关系）
   - 概念数据流图（输入、处理、输出，不含 RTL/总线细节）

2. **提取关键信息**：
   - 如果有代码：只抽取用户要求的高层组件和依赖；涉及 RTL/接口/时序时切换到专项 reference
   - 如果是文字描述：确定需要展示的节点、分组、输入输出、顺序或依赖关系

### Step 2：设计布局

1. **选择布局方向**：
   - 自下而上：适合层级结构、阶段推进
   - 自上而下：适合控制流程、仲裁流程、状态决策
   - 自左向右：适合数据流、处理链路、时序推进
   - 中心发散：适合片上互连、模块关系、多接口结构

2. **规划元素位置**：
   - 计算画布大小（通常 800-1200 宽，600-1000 高）
   - 为每个模块预留空间（节点间距至少 20-30px）
   - 考虑跨模块连接、辅助连接和注释箭头的路径

### Step 3：生成 XML（关键）

**严格按照以下模板生成，避免标签错误：**

```xml
<mxfile host="app.diagrams.net">
  <diagram name="图表名称" id="唯一id">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="900" pageHeight="800" background="#F5F5DC">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        
        <!-- 2D 节点示例 -->
        <mxCell id="2" value="节点标签" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F4CCCC;strokeColor=#333333;strokeWidth=1;fontSize=11" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="150" height="40" as="geometry"/>
        </mxCell>
        
        <!-- 3D 节点示例（用于表示立体模块、堆叠结构或强调节点） -->
        <mxCell id="3" value="" style="shape=cube;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;darkOpacity=0.05;darkOpacity2=0.1;size=20;fillColor=#B3D9E6;strokeColor=#333333;strokeWidth=1.5" vertex="1" parent="1">
          <mxGeometry x="300" y="50" width="50" height="140" as="geometry"/>
        </mxCell>
        <!-- 3D 节点的文本标签 (通常放置于图形下方独立对齐) -->
        <mxCell id="3_label" value="模块" style="text;html=1;align=center;verticalAlign=middle;fontSize=11;" vertex="1" parent="1">
          <mxGeometry x="295" y="200" width="60" height="20" as="geometry"/>
        </mxCell>

        <!-- 连线示例 -->
        <mxCell id="4" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=2;endArrow=classic" edge="1" parent="1" source="2" target="3">
          <mxGeometry relative="1" as="geometry"/>
        </mxCell>
        
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

**生成过程中的检查清单：**
- [ ] 每个 `<mxCell>` 都有对应的 `</mxCell>`（不是 `</mCell>` 或其他）
- [ ] `vertex="1"` 用于节点，`edge="1"` 用于连线
- [ ] 所有 `mxCell id` 唯一且稳定；可用连续数字或语义化 ID，不要求连续
- [ ] 连线的 `source` 和 `target` 指向存在的节点 ID
- [ ] 文本中的特殊字符已转义（`&lt;`、`&gt;`、`&amp;`）
- [ ] 所有元素都有 `parent="1"`（除了根元素 0 和 1）

### Step 4：添加辅助元素

1. **标注文本**：输入/输出标签、参数说明框、操作说明（如重复次数）、公式或维度标注
2. **视觉增强**：分组容器框、虚线辅助连接、颜色区分不同类型的组件

### Step 5：输出与说明

创建 `.drawio` 文件或输出完整 XML，运行 `python3 drawio-chip/scripts/validate_drawio.py <file.drawio>` 校验，然后按主 `SKILL.md` 的标准输出模板说明文件位置、图表用途、验证结果、使用指南、图题和导出说明。

## 标准配色方案（通用风格）

- **背景色**：`#F5F5DC`
- **输入接口 / 外设接口**：`#F4CCCC`
- **处理节点 / 核心模块**：`#B3D9E6`
- **控制节点 / 仲裁逻辑**：`#FFEB99`
- **寄存器 / SRAM / FIFO / 输出接口**：`#B6D7A8`
- **辅助说明 / 注释**：`#E6E6FA`
- **分组 / 阶段背景**：`#FFD966`
- **参数说明框**：`#FFF9E6`

## 通用图表类型模板

### 通用流程图

结构：开始/结束、步骤、判断、分支、异常路径。判断节点用菱形，分支箭头标注条件，主路径保持单一方向。

### 说明性框图

结构：中心概念、关联组件、外部输入输出、边界或分组。相关概念靠近放置，依赖关系用箭头或虚线表达。

### 轻量模块关系图

结构：模块、输入、输出、依赖关系和边界。模块用统一圆角矩形，输入输出靠边放置，主依赖方向保持一致。

## 质量保证

- **生成前**：准确理解代码/概念，确定图表类型
- **生成后**：用验证脚本检查 XML 语法、根结构、重复 ID、连线引用；再检查视觉效果（不重叠、间距合理）

## 输出模板

按主 `SKILL.md` 的标准输出模板交付：图表用途、文件路径或 XML、验证结果、核心组件、设计风格、使用说明、图题与导出说明。

## 常见问题

- "Not a diagram file"：检查 `<mxfile>`、`host`、嵌套关系
- "Opening and ending tag mismatch"：确保 `</mxCell>` 正确闭合
- 节点/连线不显示：检查 `vertex`/`edge`、`parent`、`source`/`target`
- 中文乱码：UTF-8 编码，特殊字符转义

## 注意事项

1. 连线使用 `edgeStyle=orthogonalEdgeStyle` 自动布线
2. ID 保持唯一且稳定；可按生成顺序递增，也可用语义化 ID
3. 文本换行用 `&lt;br&gt;`
4. 保持学术风格简洁
5. 宽度建议不超过 800-1000px
