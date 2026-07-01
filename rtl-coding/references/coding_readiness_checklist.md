# Coding Readiness Checklist

用于在 `rtl-coding` 开始编码前判断输入是否稳定。它只判断“能不能开始写 RTL”，不替代 `coding_standards.md`，也不替代编码完成前的代码 review。

## 使用方式

1. 从用户输入、用户指定文档或项目模块文档中提取模块设计输入。
2. 按下列 checklist 逐项判断：`pass` / `needs-clarification` / `blocked` / `not-applicable`。
3. 只要存在会影响 RTL 结构、接口、时序、异常或验证关注点的 `needs-clarification` / `blocked`，停止编码并输出阻塞反馈。
4. 不要为了通过 checklist 自行补设计决策；只能使用用户明确输入或指定文档中的信息。

## Checklist

| 项 | 检查内容 | 通过标准 |
| --- | --- | --- |
| 模块边界 | 模块职责、非职责、上下游边界、输入假设、输出承诺 | 能判断哪些逻辑属于本模块，哪些不属于本模块 |
| 接口 | 端口方向、位宽、协议、握手、背压、非法组合 | 能直接写出端口列表和接口行为 |
| 时钟复位 | 时钟域、复位类型/极性/释放语义、CDC/RDC 边界、多域假设 | 能直接写出时序块和跨域处理边界 |
| 主功能路径 | 数据通路、控制通路、关键状态转移、pipeline、buffer、arbitration | 能直接实现主路径且不需要补微架构决策 |
| 边界与异常 | 空/满、溢出/下溢、非法输入、错误检测、上报、恢复、复位后重启 | 能直接实现边界和异常行为 |
| 寄存器语义 | 配置寄存器、位域、复位值、读写属性、side effect、状态回读、中断或错误语义 | 能直接实现软件可见行为 |
| 实现约束 | 吞吐、延迟、频率/PPA、存储结构意图、允许的编码自由度 | 能判断实现方案是否符合约束 |
| CBB/IP 复用 | 是否使用已有 CBB/IP；若使用，记录 CBB/IP 模块路径 | 能判断本模块是否依赖 CBB/IP，并能定位被复用模块 |
| 验证关注点 | 主路径、边界、异常、复位恢复、实现敏感点、基本 pass/fail 观察点 | 能生成验证交接物而不只写“功能验证” |
| 冲突检查 | 用户补充、指定文档、项目约定之间是否冲突 | 没有未解决冲突 |

## Go / Stop

### Go

满足以下条件才进入编码：

- 关键 checklist 项均为 `pass` 或 `not-applicable`。
- 剩余不确定项不会影响 RTL 接口、结构、时序、异常、寄存器语义或验证关注点。
- 输入来源清楚，编码假设可追溯。

### Stop

出现以下情况时停止编码：

- 设计输入无法确定模块边界、接口、复位、主路径、异常或寄存器语义。
- 未决项会改变 RTL 结构、端口、pipeline、状态机或可见行为。
- 输入说明使用 CBB/IP，但没有给出可定位的 CBB/IP 模块路径。
- 输入来源之间冲突，且无法从用户输入或指定文档中判断优先级。
- 需要跨模块、子系统或架构决策才能继续。

## 阻塞反馈最小格式

```markdown
current_stage: rtl-coding
blocked_step: input-readiness
problem_class: spec | interface | architecture | requirement | tooling | conflict
missing_or_stale_artifacts:
  - <缺失、矛盾或失效的信息>
required_clarification_or_fix:
  - <继续编码前需要补齐或修正的内容>
reentry_step: 1. 检查输入准备度
```


## 提炼 Review Checklist

输入准备度通过后，从 `pass` 项和约束项提炼本次 `<module_name>_checklist`。该 checklist 不单独落文件，作为最终 review 时与 `coding_standards.md` 共同把关 RTL 设计的关注点。

### 生成原则

- 只从用户输入、指定文档或项目模块文档中已经明确的信息提炼，不新增设计决策。
- 每一项都写成可检查的 RTL 约束，避免“检查功能正确”这类泛泛表述。
- 每一项都应能在 RTL、`verification_input.md` 或最终回复的 review 结论中定位到证据。
- 若某类内容在输入中为 `not-applicable`，不要强行生成对应 review 项。

### 模板

```markdown
## <module_name>_checklist

### Interface and protocol
- [ ] <端口/握手/背压/非法组合约束；说明需要在 RTL 中核对的信号或行为>

### Clock and reset
- [ ] <时钟域、复位极性、复位释放、复位后状态约束>

### Main behavior
- [ ] <主数据通路、控制通路、状态机、pipeline、buffer 或 arbitration 约束>

### Boundary and exception
- [ ] <空/满、溢出/下溢、非法输入、错误上报、恢复行为约束>

### Register semantics
- [ ] <寄存器复位值、读写属性、side effect、状态回读、中断或错误语义；无寄存器时写 not-applicable>

### Implementation constraints
- [ ] <吞吐、延迟、PPA、存储结构或允许的编码自由度约束>

### CBB/IP reuse
- [ ] <若使用 CBB/IP，核对被复用模块路径；未使用时写 not-applicable>

### Verification handoff
- [ ] <verification_input.md 必须覆盖的主路径、边界、异常和实现敏感点>
```

### 示例写法

- Good: `valid_o must only assert when data_o is stable and ready_i backpressure is not blocking the transfer.`
- Good: `fifo_full must block new push requests without changing stored entries.`
- Good: `CBB/IP path must match rtl/common/sync_fifo.v when FIFO reuse is specified.`
- Bad: `check interface`。
- Bad: `make sure reset works`。
- Bad: `verify all corner cases`。
