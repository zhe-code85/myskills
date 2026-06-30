# 数字模块方案图渲染 / Microarchitecture Diagram Rendering

用于把已有 RTL/数字模块设计渲染为芯片设计文档风格的 Draw.io 方案框图。输入应提供模块、接口、层级、路径、时钟域或草图等设计内容；本文件只指导布局、风格、连线、标签和 XML 生成，不替代架构/微架构设计。

如果用户只说“画一个 XXX 方案图/微架构图”，但没有模块、接口、层级或连接关系，就先追问，不要凭空补架构。

## 核心原则

忠实呈现已有设计。模块和连接来自输入，渲染阶段只做排版、分组、视觉层级、线网整理和格式校验。若缺少关键设计信息，先追问；不要自行补全模块、接口或连接关系。

## 输入检查

在写 XML 前确认以下信息是否足够渲染：

| 输入项 | 用途 | 缺失时处理 |
| --- | --- | --- |
| 图表目标和层级 | 决定画顶层、子模块还是局部路径 | 追问需要展示的层级 |
| 模块/端口/接口 | 决定节点和边界 | 追问模块清单或已有草图 |
| 数据路径和控制路径 | 决定左右主线和控制平面 | 追问关键连接关系 |
| 时钟/复位域 | 决定域边界和颜色 | 未提供则按单域处理，不制造分区 |
| 反馈/异常/状态路径 | 决定外侧回线和状态出口 | 未提供则不臆造 |
| 用户提供风格要求 | 决定视觉语言 | 只迁移通用视觉语法，不迁移外部图内容 |

可以重排图元顺序、整理标签换行、合并视觉标注；不得改变设计语义，也不要把 `id` 改成语义字符串，仍需保留稳定的数字字符串 `id`。

## 渲染流程

### Step 1：整理输入为绘图对象

把已有设计整理为可绘制对象，而不是重新设计模块。先在内部整理一份绘图对象清单，再写 XML：

- **边界**：top/module/IP boundary、external interface、clock/reset domain。
- **节点**：输入中已有的功能模块、子模块、寄存器/FIFO/buffer、FSM/controller、状态/异常逻辑。
- **端口**：host/stream/memory/pad/irq 等外部或内部接口端点。
- **连接**：data/control/handshake/status/error/feedback 等已知关系。
- **标签**：信号名、总线名、位宽、条件、domain 名称、简短职责说明。
- **明确假设**：只记录用户已确认或输入中可以直接读出的渲染假设，例如单域显示、抽象层级、标签缩写。

只有清单中的对象可以进入 XML。若某个模块、连接、协议行为或时钟域无法追溯到输入或明确假设，不要写入 XML。

若输入只给了目标但没有结构，不要生成方案图；先请求设计结构或让上游先完成设计。

### Step 2：布局

- **默认左右布局**：输入、配置和上游接口在左；核心功能和状态在中间；输出、提交和下游接口在右。
- **数据路径**：沿左到右主通道布置，尽量直线推进。
- **控制路径**：与数据路径保持平行，作为第二条主干放在上方或下方；同时参与数据和控制的功能模块放在两条主干之间或交汇位置，作为中间交点。
- **反馈路径**：状态、错误、中断、背压优先从外侧或底部回走，不穿过主数据通道。
- **多时钟域**：用浅色域边界、标题条或域标签表示 clock domain；跨域接口靠近域边界。
- **多接口模块**：按接口方向布置端口，共享资源放中心，仲裁/反馈走外侧。
- **标签空间**：为总线/信号标签预留独立标签带或留白，标签靠近对应线段但不贴在线段中心；若文字与线相交，先移动标签或重新走线。
- **边界完整**：domain、stage、pad/interface boundary 必须完整包住所属模块；模块不得压到不属于自己的边界内。
- **画布优先**：当现有画布无法保持间距时，扩大画布、减少低价值标签或合并关系线；不要通过压缩模块、贴线标注或增加绕线来塞满画面。

#### 数据/控制平行主干规则

- 只参与数据搬运、变换、缓存或输出的模块，贴近数据主干排列。
- 只参与配置、调度、状态机、仲裁或模式控制的模块，贴近控制主干排列。
- 同时参与数据和控制的模块，放在两条主干之间或交汇位置，作为控制-数据交点。
- 控制主干到数据模块的连接应短而清晰，优先垂直或正交下发，避免长距离斜穿。
- 若输入设计已经指定不同布局或路径方向，以输入语义优先；可以调整排版，但不得改变连接含义。

背景分区只在 domain、stage、subsystem boundary 本身是输入设计的一部分时使用；不要用大色块替代结构表达。

### Step 3：放置模块

| 对象 | 推荐画法 |
| --- | --- |
| 抽象功能模块 | 直角矩形或轻量边界，短名称 + 1-2 行输入给定职责 |
| 复合模块 | 分组框或矩形，内部列输入给定的关键子职责或子模块 |
| FIFO/register/MUX/arbiter/FSM | 仅当输入设计包含或明确需要展示时画成独立子模块 |
| 接口/端口 | 贴近图边界或模块边界，名称短，方向明确 |
| status/error/irq | 靠近反馈出口，连回输入给定的控制或状态区域 |
| clock-domain boundary | 浅色边界或标题条，标注 domain/clock/reset 名称 |

模块标签保持短；长说明改为旁注。不要为了显得完整而新增未给出的子模块。

### Step 4：组织连线

1. 先画已知主数据路径，按左到右组织。
2. 再画已知控制路径，与数据路径保持空间分离。
3. 再画握手/背压路径，优先聚合为少量关系线或锚点。
4. 再画状态/错误/中断反馈，优先从外侧或底部回走。
5. clock/reset 通常作为 domain 标签或边界标签，不单独拉线到每个模块，除非输入设计要求展示。

如果线网凌乱，先调整节点位置、增加锚点、聚合关系或移动反馈路径；不要通过在线上塞文字解释混乱关系，也不要用白底文字块遮住线。

### Step 4.1：连线文字规则

- 所有 edge 单元格必须写 `value=""` 或省略 `value`；不要直接在线上输入文字。
- 不使用 Draw.io 的 edge label 机制，也不要创建 `parent` 指向 edge 的文字节点。
- 信号名、总线名、条件说明使用独立 text vertex（普通 `vertex="1"`、`parent="1"`），放在线段附近、端口旁或汇聚节点旁的留白处。
- 聚合标签应描述输入设计中的关系类别，例如 `data`, `control`, `ready/valid`, `status/error`。
- 标签默认透明背景（`fillColor=none;strokeColor=none`），不应遮挡线或模块；冲突时移动标签、增加标签带或重排走线。
- 技术框图交付时运行 `python <drawio-chip skill directory>/scripts/validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap <file.drawio>`。

### Step 5：芯片设计文档风格

- 画布默认白色，模块使用中性线框或低饱和浅色填充；避免阴影、3D、渐变和装饰性颜色。
- 字体保持一致，技术标签可用等宽字体；模块标题、端口名、信号名层级清楚。
- 强调色只用于少数关键路径、接口类别或时钟域；同一语义使用同一颜色。
- 线条使用正交路径；主路径更直接，反馈和异常走外侧。
- 图例不是默认项；如果颜色/线型含义无法从标题和标签读出，再添加极简图例。

### Step 6：XML 生成顺序

1. 写 `<mxfile>`、`<diagram>`、`<mxGraphModel>`、`<root>`。
2. 固定根节点：`<mxCell id="0"/>` 与 `<mxCell id="1" parent="0"/>`。
3. 先生成 domain/boundary，再生成模块和端口，最后生成连线与独立文字标签。
4. 保证连线 `source`/`target` 指向已存在节点。
5. 保持 XML 未压缩、缩进清晰，便于继续编辑。
6. 保存后运行 `python <drawio-chip skill directory>/scripts/validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap <file.drawio>`。

## 样式片段

### 模块

```xml
<mxCell id="20" value="Control FSM&lt;br&gt;decode / sequence" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;fontFamily=Consolas;fontSize=12;fontStyle=1" vertex="1" parent="1">
  <mxGeometry x="320" y="120" width="150" height="56" as="geometry"/>
</mxCell>
```

### 时钟域/边界

```xml
<mxCell id="21" value="clk_core domain" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F7FA;strokeColor=#8A8A8A;strokeWidth=1;dashed=1;fontFamily=Consolas;fontSize=12;fontStyle=1;align=left;verticalAlign=top;spacingLeft=8;spacingTop=6" vertex="1" parent="1">
  <mxGeometry x="220" y="70" width="520" height="260" as="geometry"/>
</mxCell>
```

### 连线与独立标签

```xml
<mxCell id="40" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#000000;strokeWidth=1;endArrow=classic" edge="1" parent="1" source="20" target="22">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
<mxCell id="41" value="load / shift / sample" style="text;html=1;align=center;verticalAlign=middle;fontFamily=Consolas;fontSize=10;fontColor=#000000;fillColor=none;strokeColor=none;" vertex="1" parent="1">
  <mxGeometry x="470" y="130" width="120" height="16" as="geometry"/>
</mxCell>
```

## 质量检查清单

- [ ] 图中模块、接口、路径和时钟域均来自已有设计输入或明确假设。
- [ ] 没有自行补全未给出的功能模块、连接关系或协议细节。
- [ ] 默认左右布局清晰；数据路径、控制路径、握手/背压、状态/错误反馈在视觉上可辨。
- [ ] 控制路径和数据路径有空间分离；控制线不穿过主数据通道。
- [ ] 多时钟域用一致的域颜色、域边界或域标题表示；单时钟域不额外制造颜色分区。
- [ ] 走线经过组织：关键路径清晰，反馈走外侧，长线不过度穿插。
- [ ] 所有 edge 的 `value` 为空；所有线旁文字是独立 text vertex，透明背景，且不挂在 edge 下。
- [ ] 文字标签不覆盖走线或模块；若位置冲突，优先移动标签或重排走线，不用白底遮线。
- [ ] domain/stage/interface 边界完整包住所属对象，模块不越界，标签和反馈线不挤占主数据通道。
- [ ] 风格像芯片设计文档，不像 PPT 装饰图或泛泛模块关系图。
- [ ] XML 可读且通过 `validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap`。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| 根据目标自行设计模块结构 | 停止生成，追问已有设计或让上游先完成设计 |
| 把外部图里的节点或连接搬到新图 | 只画当前输入设计中的节点和连接 |
| 画成上下堆叠或网状关系图 | 重排为左右数据流，并把控制路径移到独立控制平面 |
| 每个模块使用不同填充色 | 颜色只表示少量语义；多时钟域用一致的域颜色而不是随机模块颜色 |
| 走线凌乱 | 先合并信号、增加锚点或重排模块，再写 XML |
| 文字标签挡住走线 | 使用透明 text，移到线旁留白处；必要时增加标签带或重排走线 |
| 线文字直接写在 edge 上或挂在 edge 下 | 清空 edge `value`，改用 `parent="1"` 的独立 text vertex |
| XML 能打开但难编辑 | 使用稳定数字 ID、清晰缩进和独立标签节点；语义写入 `value`/label，不写入 `mxCell id` |
