# 芯片架构 / SoC 顶层框图渲染

本规则用于指导芯片架构图、SoC 顶层框图、IP block diagram 的视觉渲染方式，只约束画法和版式，不负责设计、推导或补全芯片架构。所有模块、时钟域、连接关系、特殊域边界、CDC 标记均必须来自用户输入、规格文档或已有设计材料；缺失信息只能标注为待确认，不得自行创造。若输入缺少关键架构信息，先追问。

如果用户要画的是单个 IP / module 内部的 pipeline、寄存器、FIFO、FSM、valid-ready、数据路径或控制路径，切换到 `tech-diagram.md`；本文件只处理 chip top / SoC / 子系统级架构关系。

## 输入检查

在写 XML 前确认以下信息是否足够渲染：

| 输入项 | 用途 | 缺失时处理 |
| --- | --- | --- |
| 顶层芯片 / SoC 名称 | 决定外层 chip boundary | 可用用户给定标题；未给标题则追问或用文件/模块名 |
| 子系统 / IP / block 清单 | 决定主要节点 | 缺清单时追问，不自行补 IP |
| 互连 / 总线 / crossbar | 决定中心连接结构 | 缺拓扑时追问，不猜 APB/AHB/TileLink 等连接 |
| 时钟 / 复位 / 电源 / always-on 域 | 决定 domain 容器、时钟域配色和虚线边界 | 未提供则不制造域或配色 |
| 外设 / pad / analog / IO 边界 | 决定底部或侧边接口带 | 未提供则不添加 |
| 安全 / debug / lifecycle 等系统控制路径 | 决定全局控制块和跨域连接 | 未提供则不推导 |
| 风格要求 | 决定视觉语言 | 只迁移通用视觉语法，不迁移任何外部图内容 |

## 推荐渲染流程

1. 确认输入是否包含足够的顶层名称、IP / block 清单、互连关系、domain 信息和外部边界；缺少会阻塞渲染的关键内容时先追问。
2. 先建立 chip / SoC / subsystem / special domain 的层级边界，不急于放置连线。
3. 如果输入包含 crossbar、fabric、bus matrix 或 interconnect，把它放在连接枢纽位置；没有输入则不创建。
4. 按输入中的层级、总线关系和方向性摆放 IP block。master / compute / memory / peripheral / pad / analog 等只作为输入对象的布局参考，不新增模块。
5. 根据输入决定是否表达 clock domain：没有 clock domain 信息时保持中性色；有多个 domain 时选择 IP 上色或背景容器。
6. 最后组织正交连线、添加独立透明文字标签、标注输入中明确存在的 CDC，再按质量检查清单验证 XML。

## 渲染原则
### 1. 整体风格

采用传统工程文档风格。

- 使用白色画布。
- 使用黑色或深灰色线条。
- 使用清晰的大芯片边界。
- 使用灰色层级容器表达 SoC、子系统、分区。
- 使用低饱和度淡色表达时钟域。
- 使用矩形或轻微圆角矩形表达 IP block。
- 使用正交折线连接模块。
- 不使用渐变、阴影、3D、强装饰性图标。
- 不使用高饱和度颜色作为大面积背景。

整体效果应接近 draw.io / diagrams.net 中常见的 SoC block diagram：简洁、克制、可读、工程化。

### 2. 层级边界

芯片架构图应优先建立清晰的层级边界。
推荐层级如下：
1. 芯片外边界  
2. 顶层 SoC / top module 边界  
3. 子系统或功能分区边界  
4. 时钟域或特殊域边界  
5. IP block  

常见画法：

- 芯片外边界：白底大矩形，黑色边框，左上角放芯片或项目名称。
- 顶层 SoC 边界：浅灰底矩形，黑色或深灰边框，左上角放 top 名称。
- 子系统分区：中灰底矩形，黑色边框，标题放左下角或左上角。
- IP block：淡色圆角矩形，黑色边框，文字居中。
- 特殊域：使用虚线边界叠加，不破坏原有层级。

层级不宜过多。通常最多保留芯片边界、顶层边界、子系统边界、特殊域边界四类大边界。

### 3. 中心互连 / Crossbar

SoC 顶层框图中，interconnect、crossbar、bus matrix 通常是视觉中心。

推荐画法：

- 主 crossbar 可画成横向长条、纵向长条、轻微变形矩形或沙漏形。
- crossbar 应位于连接枢纽位置。
- 输入中已经给出的 master、compute、memory、高速 IP、外设桥接等模块，可围绕 crossbar 排布；不得为了形成典型 SoC 结构而新增这些模块。
- 连线使用正交折线。
- 主数据路径可使用双向箭头。
- 控制路径使用普通单线箭头。
- 不要让大量连线穿过 IP block。

常见命名：

- `System Interconnect`
- `AXI Crossbar`
- `AHB Bus Matrix`
- `TL-UL Crossbar`
- `Peripheral Bus`
- `NoC / Fabric`

具体名称必须来自输入，不得自行替换协议或总线类型。

### 4. 时钟域配色

颜色主要用于表达 clock domain，而不是表达 IP 类型。颜色只绑定输入中明确给出的 clock / reset / power domain 名称。下表只是当用户未指定颜色时的视觉建议，不允许据此推断某个 IP 属于哪个域。

推荐使用低饱和度浅色：

| 域类型 | 推荐色感 |
| --- | --- |
| CPU / compute / high-speed domain | 浅蓝 |
| bus / interconnect domain | 蓝色或浅蓝 |
| interface / medium-speed domain | 浅粉 |
| peripheral / low-speed domain | 浅绿 |
| always-on / slow clock domain | 浅黄 |
| logic only / pad / no explicit clock | 灰色 |

颜色规则：

- 同一 clock domain 使用一致底色。
- 使用多种 clock domain 颜色时，用小型图例、域标签或边界标题解释颜色含义；未使用颜色编码时不生成图例。
- 不要给每个 IP 随机分配颜色。
- 不要把 IP 类型颜色和 clock domain 颜色混用。
- 不要用颜色暗示频率高低、功耗大小或性能强弱，除非用户明确要求并提供含义。
- 当 clock domain 信息缺失时，不应强行上色，可使用中性色并标注待确认。

### 5. 时钟域画法

时钟域有两种常用表达方式。

#### 方式 A：IP block 直接按时钟域上色

适合中小规模 SoC 图。

- 每个 IP block 根据所属 clock domain 使用对应填充色。
- 使用域标签、边界标题或必要时的小型图例解释颜色含义。
- 画面紧凑，适合模块数量较多的顶层框图。

#### 方式 B：时钟域背景容器

适合复杂 SoC 图或需要强调 clock domain boundary 的图。

- 使用半透明淡色大矩形作为 clock domain 背景。
- IP block 放在背景容器之上。
- clock domain 标题放在容器左上角或顶部。
- 背景层应放在 IP block 下面，避免遮挡模块。

默认优先采用方式 A；只有在用户明确要求突出时钟域边界、CDC 或复杂分区时，才采用方式 B。

### 6. Always-on / 特殊域

Always-on domain、retention domain、special clock domain、low-power domain 等特殊区域不应只靠颜色表达，应额外使用虚线边界。

推荐画法：

- 使用红色虚线框。
- 虚线框不填充或使用透明填充。
- 标题使用红色文字。
- 标题放在虚线框右上角或上边界附近。
- 域内 IP 仍可按所属 clock domain 使用淡色填充。

常见标签：

- `Always-on Domain`
- `AON Domain`
- `Retention Domain`
- `Low-power Domain`
- `Special Domain`

注意：

- 红色虚线只能用于少量特殊域。
- 不要给所有 clock domain 都使用红色虚线。
- 如果用户没有提供 always-on 或 low-power 信息，不得自行创建特殊域。

### 7. Pad / analog / external interface 边界

padctrl、IO mux、pad ring、analog macro、PLL、ADC/DAC、PHY 等边界类模块，只有输入提供时才绘制。

推荐画法：

- 这类模块优先贴近 chip / SoC boundary 的底部或侧边。
- digital block 到 pad / analog block 的连接应表现为边界关系，不要把外部世界的内部结构画进芯片内。
- analog boundary 可使用浅灰或无填充边界，并明确标注 `analog boundary` / `pad boundary`。
- 不要因为存在 pad / analog 边界就新增未给出的 analog IP、PHY、PLL、pad ring 或外设。

### 8. CDC 标记

跨时钟域连接可以使用轻量 CDC 标记，但不需要画成完整电路。

只有输入明确给出跨时钟域连接，或两端所属 clock domain 已明确且存在连接时，才添加 CDC 标记。CDC 类型必须来自输入；若只知道跨域但不知道机制，使用 `CDC?` 或 `CDC mechanism TBD`，不要自行选择 Async FIFO、2FF Sync 或 CDC Bridge。

推荐表达：

```text
IP A ── CDC? ── IP B
IP A ── CDC mechanism TBD ── IP B
IP A ── Async FIFO ── IP B
IP A ── CDC Bridge ── IP B
IP A ── 2FF Sync ── IP B
```

Draw.io 画法：

- CDC 可以画成连接路径中的小矩形 bridge 节点，例如 `CDC?`、`Async FIFO`、`2FF Sync`。
- 也可以使用独立透明 text vertex 放在跨域连线旁。
- 不要把 CDC 文本写入 edge `value`。
- 不要使用挂在 edge 下的 Draw.io edge label。
- 如果输入没有 clock domain 或跨域信息，不添加 CDC 标记。

### 9. 参考布局示例（仅示意，不代表架构模板）

以下 text block diagram 只用于说明一种常见 SoC 顶层框图的**版式排布方式**，用于帮助渲染时理解空间组织关系。不要把示例中的 zone、bus、infra、special domain、pad/analog band 当成必须存在的对象；只有输入中提供了对应对象时才绘制。


```text
┌────────────────────────────────────────────────────────────┐
│ <chip boundary>                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ <top SoC boundary>                                   │  │
│  │                                                      │  │
│  │  ┌───────────────┐   ┌────────────────┐   ┌───────┐ │  │
│  │  │ <left zone>   │──►│ <center bus /  │──►│<right │ │  │
│  │  │ compute/mem   │   │ interconnect>  │   │ zone> │ │  │
│  │  └───────────────┘   └────────────────┘   └───────┘ │  │
│  │                                                      │  │
│  │  ┌───────────────┐                         ┌ ┄ ┄ ┄ ┐ │  │
│  │  │ <infra zone>  │                         ┆<special│ │  │
│  │  │ clk/rst/etc.  │                         ┆domain> ┆ │  │
│  │  └───────────────┘                         └ ┄ ┄ ┄ ┘ │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ <bottom band: pads / analog / PHY / interfaces>│  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘

Example notes:
  color      = clock domain, only when provided by input
  dashed box = special domain boundary, only when provided by input
  CDC label  = explicit clock-domain crossing, only when provided by input
```

## Draw.io XML 规则

- 使用主 `SKILL.md` 的标准 `<mxfile>` 结构。
- 顶层 chip boundary、domain boundary、subsystem boundary 都是独立 vertex。
- IP / block / bus / crossbar 是独立 vertex。
- 连接是独立 edge，`value` 必须为空或省略。
- 总线名、domain 名、接口名用独立透明 text vertex 或节点标题，不使用 Draw.io edge label 机制。
- 每个 `<mxCell>` 使用唯一稳定的数字字符串 `id`；`source`、`target`、`parent` 也引用数字字符串 id。
- 特殊字符必须转义：`&` -> `&amp;`，`<` -> `&lt;`，`>` -> `&gt;`。

## 样式片段

### 顶层芯片边界

```xml
<mxCell id="10" value="chip_top" style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=14;fontStyle=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="1080" height="720" as="geometry"/>
</mxCell>
```

### 浅色 domain 容器

```xml
<mxCell id="11" value="main clock domain" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#8A8A8A;strokeWidth=1;dashed=1;fontFamily=Consolas;fontSize=12;fontStyle=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6" vertex="1" parent="1">
  <mxGeometry x="90" y="90" width="760" height="460" as="geometry"/>
</mxCell>
```

### Always-on / 特殊域虚线边界

```xml
<mxCell id="12" value="always-on domain" style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#CC0000;strokeWidth=1;dashed=1;fontFamily=Consolas;fontSize=12;fontStyle=1;fontColor=#CC0000;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6" vertex="1" parent="1">
  <mxGeometry x="880" y="90" width="190" height="260" as="geometry"/>
</mxCell>
```

### IP / block

```xml
<mxCell id="20" value="uart" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1" vertex="1" parent="1">
  <mxGeometry x="180" y="180" width="100" height="44" as="geometry"/>
</mxCell>
```

### Crossbar / interconnect

```xml
<mxCell id="30" value="main_xbar" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#E6E6E6;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1" vertex="1" parent="1">
  <mxGeometry x="430" y="250" width="180" height="72" as="geometry"/>
</mxCell>
```

### 总线连接和独立标签

```xml
<mxCell id="40" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=1;endArrow=classic" edge="1" parent="1" source="20" target="30">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
<mxCell id="41" value="TL-UL" style="text;html=1;align=center;verticalAlign=middle;fontFamily=Consolas;fontSize=10;fontColor=#000000;fillColor=none;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="305" y="190" width="70" height="18" as="geometry"/>
</mxCell>
```

## 质量检查清单

- [ ] 所有 IP、domain、interconnect、pad/analog/interface 均来自输入或用户确认的假设。
- [ ] 没有自行添加常见 SoC 模块、总线、时钟域、电源域或 debug/security 结构。
- [ ] 顶层 chip boundary、domain boundary、外围接口带层次清晰。
- [ ] Crossbar / bus / fabric 只在输入存在时绘制，并位于图的结构中心。
- [ ] 时钟域配色来自输入中的 clock domain 信息；没有 clock domain 信息时不制造彩色域。
- [ ] 连线不过度细化到每个低价值信号；总线和系统级关系清晰。
- [ ] 所有 edge 的 `value` 为空；线旁文字是独立透明 text vertex。
- [ ] XML 可读且通过 `validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap`。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| 用户只说“画 SoC 架构图”就自行补 CPU、SRAM、外设 | 停止生成，追问已有架构或 IP 清单 |
| 把外部架构样例里的模块搬到新图 | 只画用户输入中的 IP、domain、互连和边界 |
| 每个 IP 随机上色，或把时钟域配色误当成模块类别配色 | 颜色优先表示 clock domain；没有时钟域信息时保持中性配色 |
| 画成 RTL 数据通路细节图 | 回到顶层架构层级，聚合信号为 bus/fabric 关系 |
| 用线文字或白底标签遮挡连接 | 清空 edge `value`，改用透明独立 text vertex 并重排 |
