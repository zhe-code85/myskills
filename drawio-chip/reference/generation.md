# 从零生成图表

在无参考图的情况下，根据用户需求（芯片架构图、控制流程图、数据流图、数字设计状态机图等）从零生成 .drawio 图表。

## 使用时机

- 用户需要绘制芯片架构图、模块关系图、数据流图
- 用户需要绘制数字设计状态机图、状态转移图
- 用户需要绘制控制流程图、仲裁流程图、数据通路图
- 用户需要可视化芯片模块、接口关系、寄存器/存储结构或状态变化
- 用户提到「画个图」「生成架构图」「可视化结构」「绘制流程图」等需求

## 工作流程

### Step 1：需求分析

1. **确定图表类型**：
   - 芯片架构图（模块、总线、接口、存储、时钟/复位域）
   - 控制流程图（控制步骤、仲裁流程、条件分支）
   - 数据流图（输入接口、处理模块、输出接口、寄存器/存储与传输）
   - 数字设计状态机图（状态、转移条件、输入输出动作）

2. **提取关键信息**：
   - 如果有代码：分析模块层级、接口信号、数据通路、控制逻辑和状态转移
   - 如果是文字描述：确定需要展示的模块、接口、寄存器/存储、数据流或控制关系

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
- [ ] 所有 ID 唯一且连续（0, 1, 2, 3, ...）
- [ ] 连线的 `source` 和 `target` 指向存在的节点 ID
- [ ] 文本中的特殊字符已转义（`&lt;`、`&gt;`、`&amp;`）
- [ ] 所有元素都有 `parent="1"`（除了根元素 0 和 1）

### Step 4：添加辅助元素

1. **标注文本**：输入/输出标签、参数说明框、操作说明（如重复次数）、公式或维度标注
2. **视觉增强**：分组容器框、虚线辅助连接、颜色区分不同类型的组件

### Step 5：输出与说明

图表说明、使用指南、图题和导出说明。

## 标准配色方案（通用风格）

- **背景色**：`#F5F5DC`
- **输入接口 / 外设接口**：`#F4CCCC`
- **处理节点 / 核心模块**：`#B3D9E6`
- **控制节点 / 仲裁逻辑**：`#FFEB99`
- **寄存器 / SRAM / FIFO / 输出接口**：`#B6D7A8`
- **辅助说明 / 注释**：`#E6E6FA`
- **分组 / 阶段背景**：`#FFD966`
- **参数说明框**：`#FFF9E6`

## 常见图表类型模板

### 芯片架构图
结构：顶层模块、子模块、总线/互连、接口、寄存器/存储、时钟域与复位域。布局通常按数据路径从左到右、控制路径从上到下；同一层级保持对齐，跨模块连接用正交箭头，总线用较粗线或带标签箭头表示。

样式：芯片顶层边界用浅灰或浅黄大容器；计算/控制模块用浅蓝圆角矩形；寄存器、SRAM、FIFO 用浅绿圆柱或存储形状；外设/IO 接口用浅红卡片放在边界附近；总线/NoC 用粗实线或中心横条，标注位宽、方向和协议名；时钟/复位/电源域用虚线分组或淡色背景，不要和功能模块同色。

### 控制流程图
结构：开始/结束、控制步骤、判断节点、仲裁分支、异常/超时路径。判断节点使用菱形，分支箭头标注条件，主控制路径尽量保持单一方向，避免交叉。

### 数据流图
结构：输入接口、处理模块、寄存器/SRAM/FIFO、输出接口。箭头代表数据流向，箭头标签说明信号名、数据宽度、格式或有效条件；寄存器/存储节点用圆柱、存储形状或带 `REG`/`MEM` 标签的矩形，处理模块用圆角矩形。

### 数字设计状态机图
结构：状态节点、初始状态、状态转移、转移条件、输入触发、输出动作。状态使用圆角矩形或圆形节点，主路径按顺时针或从左到右排列；转移箭头标注条件，复位路径和异常路径用明显但不抢主路径的样式区分。

样式：普通状态用浅蓝圆角矩形或圆形；初始/复位状态用浅绿或双边框强调；错误/异常状态用浅红；完成/终止状态用浅紫或粗边框；状态转移用实线箭头，复位/异步跳转用虚线箭头；箭头标签统一写 `condition / action` 或 `event -> output`，避免同一张图混用多种格式。

## 质量保证

- **生成前**：准确理解代码/概念，确定图表类型
- **生成后**：XML 语法检查、逻辑完整性（连线、ID）、视觉效果（不重叠、间距合理）

## 输出模板

图表说明、核心组件、设计风格、文件信息、使用说明、图题与导出说明。详见主 SKILL 输出模板。

## 常见问题

- "Not a diagram file"：检查 `<mxfile>`、`host`、嵌套关系
- "Opening and ending tag mismatch"：确保 `</mxCell>` 正确闭合
- 节点/连线不显示：检查 `vertex`/`edge`、`parent`、`source`/`target`
- 中文乱码：UTF-8 编码，特殊字符转义

## 注意事项

1. 连线使用 `edgeStyle=orthogonalEdgeStyle` 自动布线
2. ID 按生成顺序递增
3. 文本换行用 `&lt;br&gt;`
4. 保持学术风格简洁
5. 宽度建议不超过 800-1000px