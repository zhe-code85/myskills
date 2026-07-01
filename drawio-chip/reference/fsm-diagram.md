# 状态机 / 状态迁移图渲染

用于把已有 FSM、状态表、状态转移说明、RTL `case` 状态逻辑，或用户给出的状态迁移草图渲染为可编辑 Draw.io `.drawio` 状态迁移图。输入源头可以是 RTL/SystemVerilog 片段、状态 enum、case/next-state 逻辑、设计规格、表格、文字说明、截图、已有 `.drawio` 或白板草图。

本文件只指导状态机的语义整理、视觉渲染和 Draw.io 生成；不设计新状态机，不发明状态，不把示例或模板中的状态名当成协议规则。状态名、条件、路径和说明必须来自输入或用户确认。

## FSM 渲染模式

### 严格模式

当用户明确要求“严格按 RTL”“不要推导”“signoff 图”“只按状态转移表”时使用严格模式。

规则：
- 只画输入中明确给出的状态、迁移、reset 入口和迁移条件。
- 缺状态清单、reset 状态或迁移条件时先追问。
- 不添加 inferred error path、cleanup path、默认返回边或未出现的完成路径。
- 若输入没有区分自动/条件迁移，统一用实线并说明“线型不表达自动/条件差异”。

### 工程草图模式

当输入是设计说明、流程描述、架构文档、状态作用表，而不是完整 RTL next-state 逻辑时默认使用工程草图模式。

规则：
- 可以把输入中的流程语义整理成状态迁移，但不得改写成过度精确的 RTL 条件。
- 可追溯流程迁移标为 `derived`。
- 输入描述了异常/恢复/清理语义但没有精确出口时，只有当目标状态也能从输入中找到时，才可画 `assumed_cleanup`；不得凭空新增 cleanup 状态。
- 所有 `derived` / `assumed_cleanup` 迁移必须在最终回复的来源追溯表中列出。

## FSM 输入缺口分级

### 阻塞缺口：必须追问

- 没有状态清单或状态定义。
- 没有 reset / initial 状态。
- 严格模式下缺少迁移条件。
- 同一状态、入口或出口存在多个互斥解释。
- 用户要求精确 RTL/评审签核语义，但输入只有状态作用描述。

### 可标注假设：可以画，但必须标注

- 文档给了流程步骤，但没有完整状态转移表。
- 文档给了错误、异常、恢复类型，但没有完整出口条件。
- 文档写了“返回空闲/完成后退出/继续处理”等语义，但没有精确布尔条件。
- 文档描述了循环、重试、继续处理行为，但没有完整表达式。

处理方式：
- 保留输入原词或轻量整理后的条件标签。
- 在 FSM JSON 中使用 `confidence: derived` 或 `confidence: assumed_cleanup`。
- 在图中用虚线或 notes 表达假设清理路径。
- 在最终回复列出假设和来源追溯表。

### 排版假设：可以直接处理

- 节点位置、两行/多行布局、回边走上方还是下方。
- 状态颜色强调、标签换行、图例位置。
- 页面尺寸、边界框和路径避让。

排版假设不改变 FSM 语义，最终简要说明即可。

## 推荐生成流程

优先使用通用 FSM JSON 中间表示，再用 `scripts/fsm_to_drawio.py` 生成基础 `.drawio`：

1. 提取状态、reset 状态、迁移、条件、异常/完成/返回路径。
2. 判断严格模式或工程草图模式。
3. 给每条迁移标注 `confidence`：`explicit`、`derived` 或 `assumed_cleanup`。
4. 选择通用布局模板：`linear`、`loop_2row`、`error_cleanup`、`branched` 或 `custom`。
5. 需要时在 JSON 里指定 `layout`、`route`、`label_pos` override。
6. 运行 `fsm_to_drawio.py` 生成 `.drawio`。
7. 运行 `validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap`，需要批量问题时加 `--report-all --suggest-fixes`。
8. 若脚本无法表达某个高级语义，不能静默丢弃；改用 override、分页或手工补 XML，并在最终说明中标注。

## 通用 FSM JSON 中间表示

V1 支持普通状态、reset 入口、普通迁移、虚线清理迁移、通用布局模板、坐标/走线/标签 override、notes 和来源追溯。脚本不理解具体协议或 IP 语义，只渲染输入给出的状态名与条件文本。

```json
{
  "title": "Controller FSM",
  "source": "path/to/design.md",
  "mode": "engineering_draft",
  "layout": "loop_2row",
  "reset_state": "IDLE",
  "states": [
    {"name": "IDLE", "kind": "idle", "description": "optional"},
    {"name": "RUN", "kind": "normal"},
    {"name": "ERROR", "kind": "error"}
  ],
  "transitions": [
    {
      "from": "IDLE",
      "to": "RUN",
      "label": "start && ready",
      "style": "solid",
      "confidence": "explicit",
      "source_ref": "path/to/design.md:10-12"
    },
    {
      "from": "ERROR",
      "to": "IDLE",
      "label": "error handled",
      "style": "dashed",
      "confidence": "assumed_cleanup",
      "source_ref": "path/to/design.md:40"
    }
  ],
  "notes": ["dashed edge = assumed cleanup transition"]
}
```

可选 override：

```json
{
  "states": [
    {"name": "RUN", "kind": "normal", "layout": {"x": 360, "y": 180, "w": 84, "h": 84}}
  ],
  "transitions": [
    {
      "from": "DONE",
      "to": "RUN",
      "label": "continue",
      "route": {"points": [{"x": 640, "y": 100}, {"x": 360, "y": 100}]},
      "label_pos": {"x": 460, "y": 60, "w": 120, "h": 28}
    }
  ]
}
```

## 布局模板

模板只决定图形布局，不引入任何协议/IP 语义。示例状态名只是占位，实际状态名必须来自输入。

### `linear`：线性模板

适合单向主流程：入口 -> 若干处理状态 -> 完成/返回。

规则：
- 主路径左到右。
- reset 从左侧进入 reset_state。
- 返回边走下方外圈。
- 主路径标签放状态之间的上方或下方固定标签带。

### `loop_2row`：带循环处理阶段的两行模板

适合存在“准备 -> 重复处理 -> 单元完成/判断 -> 继续或退出”的状态机，例如串行协议控制器、流处理控制器、DMA descriptor 处理器、packet parser 等。

规则：
- 上行放主处理链路。
- 循环回边从判断/完成状态返回到处理链路中的装载/启动/处理状态，走上方外圈。
- 退出路径从判断/完成状态下沉到下行。
- 下行放收尾、完成、错误/恢复等状态。
- 完成返回空闲路径走最下方或最外侧。
- 循环标签放在回边外侧留白处，不压线。

### `error_cleanup`：错误/恢复模板

适合有 ERROR、FAULT、ABORT、TIMEOUT、RECOVER 等异常状态的 FSM。

规则：
- 异常状态可用浅橙色。
- 异常入口走外圈，避免穿过主路径。
- 异常出口只连接到输入中已有的清理、恢复、完成或空闲状态。
- 若出口不是显式给出，在工程草图模式下标为 `assumed_cleanup`；严格模式下追问。
- 不把超过两行的错误条件塞进一个标签，必要时拆分。

### `branched`：分支模板

适合从一个判断状态进入多个互斥路径，例如 accept/drop、grant A/grant B、hit/miss、pass/fail。

规则：
- 分支左右或上下展开。
- 汇聚/返回路径走外圈。
- 分支条件标签靠近各自箭头，不放在同一条线上。

### `custom`：自定义模板

当状态数较多、层级复杂或自动模板导致拥挤时，使用显式 `layout`、`route`、`label_pos`。不要强行套用某个模板。

超过 15 个状态或有层级/并行状态时，优先考虑 overview + detail 多页；V1 脚本不支持的高级语义必须报错/警告或用 manual patch 标注。

## 渲染原则

- **先提取已有语义**：状态名、迁移、条件、reset 入口、异常/完成/返回路径和输出动作必须来自输入或用户确认。
- **状态节点形状**：状态默认用圆形或接近圆形的 ellipse，不用普通模块框。普通状态白底黑边；idle/done 可用浅绿色；error/fault/abort 可用浅橙色；不要用大量颜色分类。
- **初始/复位入口**：用短箭头或 `reset/start` 标签指向 reset_state；不要把 reset 画成普通业务状态。
- **迁移线型**：显式/派生主迁移用黑色实线；假设清理/恢复路径可用黑色虚线，并在 legend/notes 说明。线型含义不能靠猜。
- **迁移走线**：主路径清晰可追踪；回边、异常、重试和返回路径走外圈；双向迁移拆成两条错开的弧线或正交线。
- **条件标签**：不要把条件写进 edge `value`；用独立透明 text vertex 放在箭头附近。长条件拆成 2-3 行。标签不要贴在线段中心，不用白底文字块盖线。
- **条件写法**：保留输入里的信号名、状态名和极性。不要把自然语言条件改写成不存在于输入的协议语义。
- **图例/notes**：当使用浅色状态、虚线箭头或多种置信类型时，在空白角落放极简 legend 或 notes。
- **拥挤控制**：超过 8-10 个状态时扩大画布、分层或用模板；超过 15 个状态时考虑 overview + detail。

## Draw.io XML 规则

- 使用主 `SKILL.md` 的标准 `<mxfile>` 结构。
- 每个状态是独立 `vertex="1"` 的 ellipse。
- 每条迁移是独立 `edge="1"`，`value` 必须为空或省略。
- 条件标签是独立 text vertex，`parent="1"`，不要挂在 edge 下。
- 每个 `<mxCell>` 使用唯一稳定的数字字符串 `id`；`source`、`target`、`parent` 也引用数字字符串 id。
- 特殊字符必须转义：`&` -> `&amp;`，`<` -> `&lt;`，`>` -> `&gt;`。

## 来源追溯

FSM 图最终回复必须包含迁移来源表：

| 迁移 | 标签 | 来源 | 类型 |
| --- | --- | --- | --- |
| `state_a -> state_b` | `condition/action` | `file:line` | `explicit/derived/assumed_cleanup` |

类型含义：
- `explicit`：输入明确给出迁移或 RTL next-state 条件。
- `derived`：从流程描述整理出的迁移。
- `assumed_cleanup`：错误/恢复/清理路径假设，目标状态仍必须来自输入。

## 质量检查清单

- [ ] 所有状态、迁移、条件均来自输入或用户确认。
- [ ] 严格模式没有 derived/assumed 迁移。
- [ ] 工程草图模式的 derived/assumed 迁移已列入来源追溯表。
- [ ] 没有凭空新增状态、异常路径、完成状态或默认迁移。
- [ ] 状态节点为 ellipse，颜色只做少量语义强调。
- [ ] 所有 edge 的 `value` 为空；条件标签是独立透明 text vertex。
- [ ] 箭头、条件标签和状态节点不互相遮挡；返回/异常路径走外圈。
- [ ] XML 可读且通过 `validate_drawio.py --no-edge-labels --transparent-text-labels --no-text-line-overlap`。

## 常见错误

| 错误 | 修正 |
| --- | --- |
| 把 FSM 画成普通模块框图 | 改成状态节点 + 状态迁移箭头 |
| 根据目标自行补状态 | 停止生成，追问已有状态或 RTL 状态定义 |
| 把模板示例状态名当成规则 | 模板只决定布局；状态名必须来自输入 |
| 把条件写在 edge `value` 上 | 清空 edge `value`，改用独立 text vertex |
| 脚本不支持高级语义时静默丢弃 | 报错/警告，使用 override、分页或 manual patch |
| 线型含义靠猜 | 未给出自动/条件区别时统一实线或追问；假设 cleanup 才用虚线 |
| 大量状态随机上色 | 只用少量浅色强调 idle/done/error 等输入已有类别 |
