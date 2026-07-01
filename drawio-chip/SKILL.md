---
name: drawio-chip
description: Use this whenever the user wants to convert existing waveform, timing, digital-design, RTL, chip, SoC, IP, module, FSM, valid-ready/req-ack, data-path/control-path, or state-machine content into an editable Draw.io/diagrams.net .drawio diagram. Trigger strongly on 波形, 时序图, WaveJSON/WaveDrom, 数字设计, 数字模块方案, RTL框图, 微架构图, 状态机设计, FSM, 数据通路, 控制路径, valid-ready/req-ack, and 按参考图风格画 when the content is chip/RTL/digital-design related. If the user only asks for a generic business/process/concept Draw.io diagram, use this skill only when no more appropriate general diagram skill is available. This skill renders already-provided design content; it does not invent missing architecture or microarchitecture.
---

# Draw.io 芯片设计图渲染

本 Skill 只做**已有设计到可编辑 Draw.io `.drawio` 的转化**：把用户已经提供的芯片/RTL/数字模块设计、状态机、波形、规格说明、笔记或草图渲染/排版成图。重点是芯片设计文档风格、布局可读性和 XML 正确性。

先确认用户给的是已有设计输入；信息不足时追问关键缺口，不自行补全或发明架构。FSM 图按 `reference/fsm-diagram.md` 的严格模式/工程草图模式处理：严格模式不推导；工程草图模式只允许把输入中可追溯的流程语义整理成迁移，并标注 derived/assumed。然后根据任务类型路由到 `reference/style-migration.md`、`reference/timing-diagram.md`、`reference/fsm-diagram.md`、`reference/architecture-diagram.md`、`reference/tech-diagram.md` 或 `reference/generation.md`。

## Step 0：任务识别

| 条件 | 执行 |
|------|------|
| 用户提供参考图，并要求「按这张图的风格」画新图 | 执行 `reference/style-migration.md`；只迁移视觉风格，内容来自已有设计 |
| 用户需要绘制时序图 / 数字电路时序图 / 波形图 / 信号波形 / timing diagram / WaveJSON | 执行 `reference/timing-diagram.md`；该路径要求优先把设计说明归一为 flat WaveJSON，再用 `wavejson_to_drawio.py` 生成基础图，最后只补脚本不覆盖的注释语义 |
| 用户需要把已有 FSM、状态机设计、状态表、状态迁移说明、RTL `case` 状态逻辑或状态迁移草图转成 Draw.io 状态迁移图 | 执行 `reference/fsm-diagram.md` |
| 用户需要把已有芯片架构、SoC 顶层结构、IP 子系统清单、总线/互连拓扑、时钟/复位/电源域、pad/analog/外设边界转成 Draw.io 架构框图 | 执行 `reference/architecture-diagram.md`；只渲染已有架构，不设计、不补 IP、不补互连 |
| 用户需要把已有 RTL/数字模块设计画成方案框图、微架构框图、数据通路、控制路径、寄存器/FIFO/buffer、接口握手、总线事务或 IP 内部图 | 执行 `reference/tech-diagram.md` |
| 请求明显是非芯片/非 RTL 的通用流程图、概念关系图 | 优先不要使用本 Skill；只有没有更合适的通用 diagram skill，或用户明确要求 drawio-chip 处理时，才执行 `reference/generation.md` |

## 输入契约

- 需要已有设计输入：模块/IP/接口清单、层级、数据路径、控制路径、总线/互连拓扑、时钟/复位/电源域、状态表、状态迁移说明、反馈/异常路径、连接关系、草图、RTL 结构或上游设计说明。
- 信息不足时，只追问会阻塞转化/渲染的缺口，例如模块边界、接口方向、路径关系、时钟域、要展示的层级；不自行补全、不提出新的设计方案、不发明设计内容。
- 可以整理命名、合并视觉标签、选择布局和样式，但不得新增功能模块、改变连接含义、推导协议行为、决定架构取舍或把参考图内容搬进新图。

## 渲染原则

- 保持设计语义：图中的模块、端口、路径和域边界必须能追溯到输入内容或用户确认的假设。
- 采用芯片设计文档风格：干净画布、技术字体、直角或轻圆角模块、低饱和线框、正交信号线、清晰端口和信号标签。
- 数字模块方案图默认左右布局：上游/输入/配置在左，核心处理居中，下游/输出在右；反馈、异常和状态回写优先从外侧回走。
- 控制路径和数据路径采用平行主干布局：数据路径作为主干通常横向贯穿主体，控制路径作为第二条平行主干放在上方或下方；同时参与控制和数据的功能模块放在两条主干之间或交汇位置，作为中间交点。控制线尽量短、直、近地从控制主干下发到对应数据模块。
- 多时钟域用一致的浅色域边界、标题条或域标签表达；单时钟域不额外制造颜色分区。
- 模块按输入设计呈现：可以是抽象功能块，也可以是 FIFO、register、arbiter、MUX、FSM 等实现构件；是否展开子模块由已有设计和图表目标决定。
- 走线先组织后连接：主数据路径、控制路径、握手路径、反馈路径分层布置；跨区域关系通过锚点、汇聚节点或总线主干整理，避免线网穿插。
- 版式先自检再落 XML：预留标签带，避免模块越出所属 domain/boundary，保证主路径不被反馈线或注释挤占。
- 文字标注不遮挡走线：独立 text 标签默认透明背景，放在走线旁的留白/标签带；不要把标签贴在线段中心，不要用白底文字块盖住线，冲突时移动标签或重排走线。
- 禁止把文字写进连线本身：所有 edge `value` 必须为空，也不要使用挂在 edge 下的 Draw.io edge label 机制。信号名、总线名、条件说明必须用独立 text vertex（普通 `vertex="1"`、`parent="1"`）放在线旁或总线旁。
- 避免汇报式装饰：不默认生成彩虹模块、圆柱 3D 存储、legend、阴影和无语义的大圆角盒子；若画面像泛泛模块关系图，重新按数据/控制/反馈路径排版。

## 交付原则

- 产物必须是可编辑 `.drawio` 文件或完整 `.drawio` XML；不要只输出图表说明。
- 如果缺少足以渲染的设计输入，先追问关键缺口。
- 写入 `.drawio` 前检查目标路径是否已存在：不存在可直接创建；存在则先 Read。若确认是同一任务旧产物，可以覆盖；若内容明显不属于当前任务，生成新文件名或询问用户。
- FSM 图优先先整理为通用 FSM JSON 中间表示，再用 `scripts/fsm_to_drawio.py` 生成基础 `.drawio`。脚本只理解通用状态机概念，不理解具体协议/IP 语义；状态名、条件和说明必须来自输入。遇到脚本暂不支持的高级语义，不要静默丢弃：优先使用 layout/route/label override，仍无法表达时生成基础图后手工补 XML，并在最终说明中标注 manual patch。
- 生成 `.drawio` 后运行本 skill 目录下的 `scripts/validate_drawio.py`；技术框图、FSM、流程关系类连线图加 `--no-edge-labels --transparent-text-labels --no-text-line-overlap`，需要一次性定位多个布局问题时加 `--report-all --suggest-fixes`；时序图/波形图只加 `--no-edge-labels --transparent-text-labels`。若用户只要 XML 文本，用 `-` 从 stdin 校验。时序图/波形图必须先把设计说明、信号列表或逐拍关系归一成 flat WaveJSON，再走本 skill 目录下的 `scripts/wavejson_to_drawio.py` 生成基础 `.drawio`；不要直接从自然语言或接口说明手写整张 XML。该脚本只覆盖 flat WaveJSON：`signal[].name`、`signal[].wave`、可选 `signal[].data` 和可选顶层 `title`。遇到 grouped signals、`node`/`edge`、`period`、`phase`、`head`、`foot`、`config` 等 WaveDrom 扩展时，不要静默丢语义；先让脚本报出不支持项，再手工渲染这些采样、setup/hold、阶段标注、延迟箭头或说明文字。
- 最终回复必须包含：图表用途、文件路径或 XML 块、验证结果、Draw.io 打开方式、需要用户确认的假设。FSM 图还必须包含模式（严格模式/工程草图模式）和迁移来源追溯表。

## XML 格式严格性

- 所有标签必须正确闭合：`<mxCell>` 对应 `</mxCell>`。
- 使用 `vertex="1"` 标记节点，`edge="1"` 标记连线。
- 每个 `<mxCell>` 必须有唯一且稳定的**数字字符串** `id`，例如 `0`, `1`, `2`, `3`；连线 `source`/`target` 和节点/连线 `parent` 也必须引用数字字符串 id。不要使用 `apb`, `ctrl_to_shift`, `sig_0_wave` 这类语义字符串作为 cell id，因为 Draw.io 客户端在某些路径下会打开失败。
- 特殊字符必须转义：`&` -> `&amp;`，`<` -> `&lt;`，`>` -> `&gt;`。
- 保持 XML 缩进和可读性，便于用户继续编辑。

## 标准文件结构

```xml
<mxfile host="app.diagrams.net">
  <diagram name="diagram-name" id="diagram-id">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" background="#FFFFFF">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- domains/boundaries, modules/ports, edges, standalone text labels -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 常用样式

- **中性模块**：`rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1`
- **浅色功能模块**：`rounded=0;whiteSpace=wrap;html=1;fillColor=#F7F9FA;strokeColor=#333333;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1`
- **轻量边界框**：`rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#D1D1D1;strokeWidth=1;dashed=1;fontFamily=Consolas;fontSize=12;fontStyle=1`
- **时钟域/分区背景（仅必要时）**：`rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#8A8A8A;strokeWidth=1;dashed=1;fontSize=14;fontStyle=1`
- **竖向 pipeline/register/buffer**：`rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#333333;strokeWidth=1;fontSize=12;fontStyle=1;rotation=-90`
- **MUX/选择器**：`shape=trapezoid;direction=east;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#333333;strokeWidth=1;fontSize=11`
- **状态/异常椭圆**：`ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#333333;strokeWidth=1;fontSize=12;fontStyle=1`
- **主信号线**：`edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=1;endArrow=classic`，`value=""`
- **可选强调线**：`edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#505050;strokeWidth=1;endArrow=classic`，`value=""`；仅用于少数关键路径或接口类别
- **反馈/异常/辅助线**：`edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=1;endArrow=classic;dashed=1`
- **信号/总线文字**：独立 text 节点，使用 `vertex="1"`、`parent="1"`，不要挂在 edge 下，默认透明背景；例如 `text;html=1;align=center;verticalAlign=middle;fontSize=11;fontColor=#333333;fillColor=none;strokeColor=none`

## 输出模板

```text
图表用途：...
文件：path/to/file.drawio
验证：
- 技术框图/FSM/流程关系图：python <drawio-chip skill directory>/scripts/validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap path/to/file.drawio -> OK
- 时序图/波形图：python <drawio-chip skill directory>/scripts/validate_drawio.py --no-edge-labels --transparent-text-labels path/to/file.drawio -> OK
说明：采用的芯片设计文档风格、布局、路径分离、时钟域/边界表达...
Draw.io：打开 https://app.diagrams.net/，选择 File > Open From > Device。
假设：...
```

## 参考资源

- Draw.io：https://app.diagrams.net/
- 官方文档：https://www.drawio.com/doc/
