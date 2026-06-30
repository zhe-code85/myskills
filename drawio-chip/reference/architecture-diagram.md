# 芯片架构 / SoC 顶层框图渲染

用于把已有芯片架构、SoC 顶层结构、IP 子系统清单、总线/互连拓扑、时钟/复位/电源域、外设/pad/analog 边界等内容渲染为可编辑 Draw.io `.drawio` 架构框图。

本文件只做**已有架构内容的画图和排版**，不做芯片架构设计，不新增 IP，不补总线拓扑，不决定 clock/reset/power domain，不推导安全域、地址空间、外设连接或系统层级。若输入缺少关键架构信息，先追问。

顶层 SoC block diagram 常见的视觉语法是大芯片边界、中心互连/crossbar、外围 IP 分区、底部 pad/analog/外部接口带、角落图例；其中不同底色主要表达**时钟域配色**，少量虚线强调 always-on 或特殊域边界。

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

## 渲染原则

- **忠实呈现已有架构**：只画输入中给出的 IP、子系统、互连、域、pad/analog/interface 和连接关系。不要为了“完整 SoC”自行补 CPU、SRAM、DMA、debug、clock manager、reset manager、UART、SPI 等常见模块。
- **顶层边界优先**：用一个大外框表达 chip / SoC top boundary，标题放左上或顶部。内部再放 domain、subsystem、crossbar、IP blocks。
- **中心互连结构**：如果输入给出 crossbar / fabric / bus matrix，把它放在图中心或偏中心，作为主要汇聚节点；主机、存储、外设、系统控制块围绕它分布。若互连不是输入的一部分，不要凭空添加。
- **domain 容器**：clock domain 使用浅灰或低饱和底色表达，这是 SoC 顶层图中最优先、最稳定的配色语义。power/reset/security/always-on 等非时钟域若需要表达，优先用边框、虚线、标题或图例补充，不要和时钟域配色混淆。域标题放容器左上角，容器完整包住所属模块。单域设计不额外制造彩色分区。
- **always-on / 特殊域**：可用红色或强调色虚线边界表达 always-on / special domain，但只有输入明确给出时才使用；不要让红色承担唯一语义，必要时在图例说明。
- **外围与 pad 带**：pad、analog、external interface、IO mux 等外围对象优先放在底部或外侧边缘，形成清晰接口带；内部数字 IP 不应压到 pad/analog 边界里。
- **布局层次**：系统控制/生命周期/debug/clock/reset 这类全局控制块放在上方或侧边；计算/存储/外设围绕互连；pad/analog/外部连接放边缘。以输入架构为准，布局只服务阅读。
- **连接策略**：架构图不需要画每一根信号。优先画 bus/fabric 级连接、domain 级关系和关键控制路径。大量重复外设可聚合为分组或少量总线连接，并用标签说明。
- **颜色语义**：颜色优先用于时钟域配色；同一 clock domain 使用同一低饱和底色。不要用颜色随机区分每个 IP。若还需要表达 power/security/always-on 等其他域，优先用虚线边界、边框颜色或图例，而不是新增一套互相冲突的填充色。
- **图例**：当颜色、虚线边界或线型有语义时，在角落放极简 legend。若图中只有普通 block 和普通连接，不强行加图例。
- **拥挤控制**：SoC 顶层图通常模块多。优先扩大画布、分区、聚合重复 IP、减少低价值线；不要让连接线穿越大量模块，也不要用文字遮线。

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
