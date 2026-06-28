# 时序图 / 波形图（Timing Diagram）

用 Draw.io 精确绘制数字电路的**通用时序图 / 波形图**。不要先套某个协议模板；应先把用户需求拆成底层波形原语：时钟、单 bit 电平、多 bit 总线、跳变、脉冲、未知态、高阻态、采样点、setup/hold 窗口、延迟箭头、分组与间隔。

核心原则：用 **WaveJSON（WaveDrom）逐拍符号**描述信号语义，用 Draw.io 的折线边（`edge + Array(points) + endArrow=none`）按拍推导坐标，最终产出可在 Draw.io 打开、编辑、导出 PNG/SVG 的 `.drawio` XML。

## 使用时机

- 用户提到「数字电路时序图」「波形图」「信号波形」「timing diagram」「WaveJSON」「时钟信号」「信号时序」「总线时序」
- 数字逻辑：复位、使能、寄存器读写、状态机、组合逻辑延迟、上电时序
- 接口时序：SPI / I2C / UART / AXI / valid-ready / req-ack / 建立保持时间
- 用户给出 WaveJSON、信号列表、bit 序列、电平变化描述，要求画成 Draw.io 图

## WaveJSON 符号速查

每个字符代表一个**节拍（beat）**，`.` 表示延续上一拍。

| 符号 | 语义 | Draw.io 表达 |
| --- | --- | --- |
| `0` | 低电平 | `Y_low` 水平线；与前拍不同则在拍边界插垂直跳变 |
| `1` | 高电平 | `Y_high` 水平线；与前拍不同则在拍边界插垂直跳变 |
| `l` / `h` | 低 / 高，但不强调跳变 | 水平线；必要时断开或弱化跳变 |
| `.` | 延续上一状态 | 水平延伸，无新语义 |
| `p` | 正向时钟周期 | 前半拍高、后半拍低的方波 |
| `n` | 反向时钟周期 | 前半拍低、后半拍高的方波 |
| `P` / `N` | 带边沿标记的时钟 | 方波 + 采样箭头 / 三角标记 |
| `=` | 数据总线有效区间 | 上下双线夹 + 中心 data 文字 |
| `2` `3` `4` `5` | 数据总线分组 | 同 `=`，但换背景/线色区分阶段 |
| `x` / `u` | 未知 / don't care | 区间内画 X 斜线或交叉填充 |
| `z` | 高阻态 | 中线 `Y_mid` 单线，常配 `Z` 文本 |
| `d` | 默认 / 空闲 / 未指定 | 中线或淡色水平线 |
| `|` | 时间间隔 / 关键边界 | 垂直强调线，不属于某一信号 |

配套字段：

```json
{ signal: [
  { name: "clk", wave: "p......." },
  { name: "sig", wave: "0.1.0..1" },
  { name: "bus", wave: "x.==.2.z", data: ["A", "B", "C"] }
]}
```

## 坐标系统

### 网格参数

| 参数 | 含义 | 默认 |
| --- | --- | --- |
| `CW` | 每拍宽度 | `40` |
| `CH` | 每行高度 | `40` |
| `LW` | 左侧信号名区宽 | `90` |
| `pad` | 行间距 | `10` |
| `X0` | 波形起点 X | `100` |
| `Y0` | 第一行 top | `60` |

节拍边界：`X(beat) = X0 + beat × CW`。半拍边界：`X_half(beat) = X0 + beat × CW + CW/2`。

### 每行 Y 基准

信号行 `i` 从 0 起：

```text
row_top    = Y0 + i × (CH + pad)
row_bottom = row_top + CH
Y_high     = row_top + 8
Y_low      = row_bottom - 8
Y_mid      = (Y_high + Y_low) / 2
```

所有跳变点、采样点、网格线必须落在节拍或半拍边界上，避免渲染后出现毛刺或错位。

## 基础表达原语

画时序图时优先覆盖这些底层表达方式：

| 表达方式 | 用途 | 关键画法 |
| --- | --- | --- |
| 电平保持 | reset / enable / valid / ready 等单 bit 信号 | 高低两条水平基准线，保持期间不变 |
| 上升沿 / 下降沿 | 触发、释放、开始、结束 | 在节拍边界插垂直段 |
| 周期时钟 | 全局时钟、接口时钟 | 每拍固定高低翻转，可标采样沿 |
| 宽脉冲 / 窄脉冲 | strobe、ack、irq、one-shot | 宽脉冲占整拍，窄脉冲占半拍或 1/4 拍 |
| 有效窗口 | 数据有效、事务进行中 | 用单 bit 高/低区间或浅色背景块表示 |
| 多 bit 总线 | addr/data/cmd/state | 上下双线夹 + data 文本，切换处对齐 |
| 总线切换 | A→B、cmd→data、phase change | WaveJSON 风格斜边收束/展开，不用简单竖线 |
| 未知态 X | 复位前、无效区、不关心 | X 斜线或斜纹区 |
| 高阻态 Z | 三态、IO 释放、总线空闲 | 中线 + `Z`/`Hi-Z` 标签 |
| 采样点 | 哪个时钟沿捕获数据 | 垂直线 / 小三角 / 箭头指向数据区 |
| setup/hold | 采样前后稳定时间 | 双向箭头 `t_su` / `t_h` |
| 传播延迟 | 输入跳变到输出响应 | 跨信号箭头 `t_pd` / `t_co` |
| 周期/宽度标注 | `Tclk`、`t_high`、`t_low` | 水平双向箭头标尺寸 |
| 间隔/省略 | 长事务省略中间拍 | `|` 垂直线或 `//` 断点 |
| 阶段分组 | init/active/wait/done | 顶部浅色横条或大括号 |

### 1. 时钟（clock）

用途：系统时钟、采样时钟、接口时钟。

WaveJSON：

```json
{ name: "clk", wave: "p......." }
```

Draw.io 表达：每一拍由 4 段组成：

```text
(X, Y_high) -> (X+CW/2, Y_high)
            -> (X+CW/2, Y_low)
            -> (X+CW, Y_low)
```

如果要画反相时钟 `n`，交换 `Y_high` / `Y_low`。如果要强调采样边沿，在上升沿或下降沿位置放小三角（`shape=triangle`）或短箭头。

### 2. 单 bit 信号（level signal）

用途：reset、enable、valid、ready、irq、cs、busy 等。

WaveJSON：

```json
{ name: "enable", wave: "0.1..0.1" }
```

Draw.io 表达：低电平画 `Y_low`，高电平画 `Y_high`；每次 `0↔1` 变化时，在拍边界插入垂直段。

```text
0 -> 1: (X, Y_low)  -> (X, Y_high)
1 -> 0: (X, Y_high) -> (X, Y_low)
```

### 3. 脉冲（pulse）

用途：one-shot、write strobe、interrupt pulse、ack pulse。

WaveJSON：

```json
{ name: "pulse", wave: "0.10.10." }
```

Draw.io 表达：本质是单 bit 信号的短高电平窗口。窄脉冲可用半拍宽度：`X + CW/4` 到 `X + 3CW/4`，不要强行塞进 1px 竖线，否则导出 PNG 后不清楚。

### 4. 复位 / 使能窗口（reset / enable window）

用途：上电复位、低有效复位、时钟门控、事务有效窗口。

WaveJSON：

```json
{ name: "rst_n", wave: "0..1...." }
{ name: "en",    wave: "0.111.0." }
```

Draw.io 表达：

- 低有效复位：标签用 `rst_n` 或 `RESET#`，低电平区间可加浅红背景块。
- 有效窗口：在信号高电平区间下方加半透明浅色矩形，或用两条垂直边界线标出窗口。

### 5. 多 bit 总线（data bus）

用途：地址、数据、状态码、命令字段、多 bit 控制字。

WaveJSON：

```json
{ name: "addr[7:0]", wave: "x.==.2.z", data: ["A0", "A1", "D0"] }
```

Draw.io 表达：

- 有效总线区间：上下两条平行线（`Y_high` / `Y_low`）包住区间。
- 区间文字：在 `(X_start+X_end)/2, Y_mid` 放 `data` 文本。
- 总线切换：默认用 WaveJSON 风格的斜边收束/展开：上一段上下线在切换边界前收束到 `Y_mid`，下一段从 `Y_mid` 展开到上下线，形成连续的沙漏/六边形过渡；只有极简草图才用竖线切换。
- 分组色：`=` 默认黑线；`2/3/4/5` 可配浅紫、浅绿、浅蓝、浅橙背景。

### 6. 未知态 / don't care（X）

用途：复位前未知、无效窗口、未驱动但不关心的总线值。

WaveJSON：

```json
{ name: "data", wave: "xx==xx", data: ["D0", "D1"] }
```

Draw.io 表达：在该区间画 X 形斜线：

```text
(X0, Y_high) -> (X1, Y_low)
(X0, Y_low)  -> (X1, Y_high)
```

如果区间较长，可加淡灰背景并重复斜纹；短区间用一个 X 即可。

### 7. 高阻态（Z）

用途：三态总线、IO 释放、open-drain、总线空闲。

WaveJSON：

```json
{ name: "io", wave: "z.=.z" , data: ["DRIVE"] }
```

Draw.io 表达：高阻区间画 `Y_mid` 中线，并可放 `Z` 或 `Hi-Z` 文本。不要把 `z` 画成 X；`x` 是值未知，`z` 是没有驱动。

### 8. 采样边沿（sample edge）

用途：说明数据在哪个时钟沿被采样。

WaveJSON 常见写法：用 `node` / `edge` 表示采样关系。

```json
{ name: "clk",  wave: "p...", node: ".a.." }
{ name: "data", wave: "x=..", node: ".b..", data: ["D"] }
{ edge: ["a->b sample"] }
```

Draw.io 表达：

- 在采样时钟沿放小三角或短竖线。
- 从采样边沿画箭头指向被采样的数据区间。
- 箭头文字用 `sample`、`latch`、`capture` 或中文「采样」。

### 9. 建立 / 保持时间（setup / hold）

用途：触发器输入要求、接口采样约束。

WaveJSON 可用 `node` 标记采样边沿与数据稳定区间；Draw.io 里更直观：

- 采样边沿：一条垂直虚线或三角标记。
- `t_su`：从数据稳定开始到采样边沿的双向箭头。
- `t_h`：从采样边沿到数据允许变化点的双向箭头。
- 数据稳定窗口：总线或单 bit 水平段保持不变，不要在 setup/hold 窗口内画跳变。

### 10. 传播延迟 / 响应延迟（delay arrow）

用途：`req -> ack`、`clk -> q`、输入变化到输出变化。

Draw.io 表达：

- 从源信号的跳变点画箭头到目标信号的响应跳变点。
- 箭头标签写 `t_pd`、`t_co`、`latency`、`N cycles`。
- 若跨多拍，箭头可画成折线，避免穿过信号名和数据文字。

### 11. 间隔 / 分组 / 省略（gap / group / break）

用途：长事务中省略中间拍、区分配置阶段/数据阶段/空闲阶段。

WaveJSON：`|` 表示关键时间边界或视觉间隔。

Draw.io 表达：

- `|`：贯穿所有信号行的垂直强调线。
- 分组：上方用浅色横条或大括号标注 `Init` / `Transfer` / `Idle`。
- 省略：用两条短斜杠 `//` 放在所有信号行同一 X 位置。

## 通用生成流程

1. **识别信号类型**：clock / single-bit / bus / x / z / annotation。
2. **确定节拍数**：取最长 `wave` 字符串长度；若有 `|`，按实际节拍边界单独画垂直标记。
3. **建立坐标网格**：用 `CW=40`、`CH=40`、`X0=100`、`Y0=60` 开始；信号多时增大 pageHeight。
4. **逐行生成波形**：每行独立计算 `Y_high/Y_low/Y_mid`，逐拍转换为折线点。
5. **补总线文字**：每个有效总线片段消耗一个 `data` 文本，居中放置。
6. **补注释元素**：采样箭头、setup/hold 双向箭头、阶段背景、垂直边界线。
7. **自检**：所有跳变点 X 对齐，文本不压线，X/Z 区分清楚，箭头不穿过主要文字。
8. **校验**：保存为 `.drawio` 后运行 `python3 drawio-chip/scripts/validate_drawio.py <file.drawio>`；验证失败先修 XML。

## 通用示例：基础波形原语合集

这个模板故意不绑定任何协议，只展示基础表达：时钟、单 bit 跳变、脉冲、多 bit 总线、未知态、高阻态、采样边界、setup/hold 标注。

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Timing Primitives" id="timing-primitives">
    <mxGraphModel dx="1000" dy="700" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="520" pageHeight="380" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="CLK" style="text;html=1;align=right;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="10" y="60" width="80" height="40" as="geometry"/></mxCell>
        <mxCell id="3" value="SIG" style="text;html=1;align=right;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="10" y="110" width="80" height="40" as="geometry"/></mxCell>
        <mxCell id="4" value="PULSE" style="text;html=1;align=right;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="10" y="160" width="80" height="40" as="geometry"/></mxCell>
        <mxCell id="5" value="BUS[3:0]" style="text;html=1;align=right;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="10" y="210" width="80" height="40" as="geometry"/></mxCell>
        <mxCell id="6" value="IO" style="text;html=1;align=right;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="10" y="260" width="80" height="40" as="geometry"/></mxCell>

        <mxCell id="10" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="55" as="sourcePoint"/><mxPoint x="100" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="11" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="140" y="55" as="sourcePoint"/><mxPoint x="140" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="12" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="180" y="55" as="sourcePoint"/><mxPoint x="180" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="13" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="220" y="55" as="sourcePoint"/><mxPoint x="220" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="14" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="260" y="55" as="sourcePoint"/><mxPoint x="260" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="15" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="300" y="55" as="sourcePoint"/><mxPoint x="300" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="16" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="340" y="55" as="sourcePoint"/><mxPoint x="340" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="17" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="380" y="55" as="sourcePoint"/><mxPoint x="380" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="18" value="" style="endArrow=none;html=1;dashed=1;strokeColor=#CCCCCC;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="420" y="55" as="sourcePoint"/><mxPoint x="420" y="305" as="targetPoint"/></mxGeometry></mxCell>

        <mxCell id="20" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;rounded=0;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="68" as="sourcePoint"/><mxPoint x="420" y="92" as="targetPoint"/><Array as="points"><mxPoint x="120" y="68"/><mxPoint x="120" y="92"/><mxPoint x="140" y="92"/><mxPoint x="140" y="68"/><mxPoint x="160" y="68"/><mxPoint x="160" y="92"/><mxPoint x="180" y="92"/><mxPoint x="180" y="68"/><mxPoint x="200" y="68"/><mxPoint x="200" y="92"/><mxPoint x="220" y="92"/><mxPoint x="220" y="68"/><mxPoint x="240" y="68"/><mxPoint x="240" y="92"/><mxPoint x="260" y="92"/><mxPoint x="260" y="68"/><mxPoint x="280" y="68"/><mxPoint x="280" y="92"/><mxPoint x="300" y="92"/><mxPoint x="300" y="68"/><mxPoint x="320" y="68"/><mxPoint x="320" y="92"/><mxPoint x="340" y="92"/><mxPoint x="340" y="68"/><mxPoint x="360" y="68"/><mxPoint x="360" y="92"/><mxPoint x="380" y="92"/><mxPoint x="380" y="68"/><mxPoint x="400" y="68"/><mxPoint x="400" y="92"/></Array></mxGeometry></mxCell>
        <mxCell id="21" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;rounded=0;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="142" as="sourcePoint"/><mxPoint x="420" y="118" as="targetPoint"/><Array as="points"><mxPoint x="180" y="142"/><mxPoint x="180" y="118"/><mxPoint x="260" y="118"/><mxPoint x="260" y="142"/><mxPoint x="340" y="142"/><mxPoint x="340" y="118"/></Array></mxGeometry></mxCell>
        <mxCell id="22" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;rounded=0;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="192" as="sourcePoint"/><mxPoint x="420" y="192" as="targetPoint"/><Array as="points"><mxPoint x="140" y="192"/><mxPoint x="140" y="168"/><mxPoint x="180" y="168"/><mxPoint x="180" y="192"/><mxPoint x="260" y="192"/><mxPoint x="260" y="168"/><mxPoint x="300" y="168"/><mxPoint x="300" y="192"/></Array></mxGeometry></mxCell>

        <mxCell id="30" value="" style="rounded=0;html=1;fillColor=#FFFBE6;strokeColor=none;" vertex="1" parent="1"><mxGeometry x="140" y="217" width="80" height="26" as="geometry"/></mxCell>
        <mxCell id="31" value="" style="rounded=0;html=1;fillColor=#E3F2FD;strokeColor=none;" vertex="1" parent="1"><mxGeometry x="220" y="217" width="80" height="26" as="geometry"/></mxCell>
        <mxCell id="32" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="140" y="218" as="sourcePoint"/><mxPoint x="210" y="218" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="33" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="140" y="242" as="sourcePoint"/><mxPoint x="210" y="242" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="34" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="210" y="218" as="sourcePoint"/><mxPoint x="220" y="230" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="35" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="210" y="242" as="sourcePoint"/><mxPoint x="220" y="230" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="36" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="220" y="230" as="sourcePoint"/><mxPoint x="230" y="218" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="37" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="220" y="230" as="sourcePoint"/><mxPoint x="230" y="242" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="38" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="230" y="218" as="sourcePoint"/><mxPoint x="300" y="218" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="39" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="230" y="242" as="sourcePoint"/><mxPoint x="300" y="242" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="40" value="" style="endArrow=none;html=1;strokeColor=#888888;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="218" as="sourcePoint"/><mxPoint x="140" y="242" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="41" value="" style="endArrow=none;html=1;strokeColor=#888888;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="242" as="sourcePoint"/><mxPoint x="140" y="218" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="42" value="A" style="text;html=1;align=center;verticalAlign=middle;fontSize=12;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="140" y="222" width="80" height="16" as="geometry"/></mxCell>
        <mxCell id="43" value="B" style="text;html=1;align=center;verticalAlign=middle;fontSize=12;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="220" y="222" width="80" height="16" as="geometry"/></mxCell>
        <mxCell id="44" value="" style="endArrow=none;html=1;strokeColor=#888888;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="300" y="218" as="sourcePoint"/><mxPoint x="340" y="242" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="45" value="" style="endArrow=none;html=1;strokeColor=#888888;strokeWidth=1;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="300" y="242" as="sourcePoint"/><mxPoint x="340" y="218" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="46" value="Z" style="text;html=1;align=center;verticalAlign=middle;fontSize=12;fontColor=#777777;" vertex="1" parent="1"><mxGeometry x="340" y="222" width="40" height="16" as="geometry"/></mxCell>

        <mxCell id="50" value="" style="endArrow=none;html=1;strokeColor=#777777;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="100" y="280" as="sourcePoint"/><mxPoint x="180" y="280" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="51" value="Z" style="text;html=1;align=center;verticalAlign=middle;fontSize=12;fontColor=#777777;" vertex="1" parent="1"><mxGeometry x="120" y="272" width="40" height="16" as="geometry"/></mxCell>
        <mxCell id="52" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="180" y="268" as="sourcePoint"/><mxPoint x="300" y="268" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="53" value="" style="endArrow=none;html=1;strokeColor=#333333;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="180" y="292" as="sourcePoint"/><mxPoint x="300" y="292" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="54" value="DRIVE" style="text;html=1;align=center;verticalAlign=middle;fontSize=12;fontColor=#333333;" vertex="1" parent="1"><mxGeometry x="190" y="272" width="100" height="16" as="geometry"/></mxCell>
        <mxCell id="55" value="" style="endArrow=none;html=1;strokeColor=#777777;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="300" y="280" as="sourcePoint"/><mxPoint x="420" y="280" as="targetPoint"/></mxGeometry></mxCell>

        <mxCell id="60" value="" style="endArrow=none;html=1;strokeColor=#B85450;strokeWidth=2;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="220" y="55" as="sourcePoint"/><mxPoint x="220" y="305" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="61" value="sample" style="text;html=1;align=center;fontSize=11;fontColor=#B85450;" vertex="1" parent="1"><mxGeometry x="195" y="35" width="50" height="18" as="geometry"/></mxCell>
        <mxCell id="62" value="t_su" style="endArrow=block;startArrow=block;html=1;rounded=0;strokeColor=#6C8EBF;fontColor=#6C8EBF;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="180" y="320" as="sourcePoint"/><mxPoint x="220" y="320" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="63" value="t_h" style="endArrow=block;startArrow=block;html=1;rounded=0;strokeColor=#82B366;fontColor=#82B366;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="220" y="340" as="sourcePoint"/><mxPoint x="260" y="340" as="targetPoint"/></mxGeometry></mxCell>
        <mxCell id="64" value="图：基础时序图原语（时钟、单 bit、脉冲、总线、X、Z、采样、setup/hold）" style="text;html=1;align=center;fontSize=12;fontColor=#666666;fontStyle=2;" vertex="1" parent="1"><mxGeometry x="70" y="355" width="390" height="20" as="geometry"/></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

等价 WaveJSON（语义对照，不要求 Draw.io 像素级一致）：

```json
{ signal: [
  { name: "CLK",      wave: "p......." },
  { name: "SIG",      wave: "0.1.0.1." },
  { name: "PULSE",    wave: "010.10.." },
  { name: "BUS[3:0]", wave: "x.=.2.xz", data: ["A", "B"] },
  { name: "IO",       wave: "z.=...z.", data: ["DRIVE"] }
]}
```

## 组合原则

不要从某个固定协议模板开始画。先把用户描述拆成下面这些基础元素，再按时间轴组合：

1. 哪些信号是 clock，哪些是单 bit，哪些是多 bit bus。
2. 每个信号的初始状态是什么：高、低、未知 `x`、高阻 `z`。
3. 哪些拍发生跳变：上升沿、下降沿、窄脉冲、总线数据切换。
4. 哪些区间需要表达有效窗口、无效窗口、空闲窗口、等待窗口。
5. 哪些时间点需要强调：采样边沿、分组边界、省略断点。
6. 哪些约束需要标注：setup/hold、传播延迟、响应延迟、周期宽度。

最终图应该像一组可复用的波形原语组合，而不是某个具体协议的套壳。

## XML 检查清单

- 每个 `<mxCell>` 要么自闭合，要么有 `</mxCell>`；`sourcePoint` / `targetPoint` 必须在 `<mxGeometry>` 内。
- 所有 `id` 唯一且稳定，建议按功能分段编号（标签 2–9，网格 10–19，波形 20+，注释 60+）。
- `&`、`<`、`>` 必须写成 `&amp;`、`&lt;`、`&gt;`。
- 波形边统一 `endArrow=none;rounded=0;strokeWidth=2`；箭头注释才使用 `endArrow`。
- 总线有效区、背景块、文字必须按 z-order 排列：背景块在前，波形线在后，文字最后。
- 图题放在最下方，不要压住 setup/hold 箭头或总线文字。
- 交付前必须通过 `validate_drawio.py` 的结构、ID、edge 引用检查。

## 常见问题

- **画成协议模板而不是通用时序图**：先拆原语，再组合；不要默认生成 SPI / I2C，除非用户明确要求协议。
- **单 bit 与总线混淆**：单 bit 是一条方波线；总线是上下双线夹 + 文本。
- **`x` 和 `z` 混淆**：`x` 是未知 / 不关心，用 X 斜线；`z` 是高阻 / 无驱动，用中线 + `Z`。
- **setup/hold 窗口里有跳变**：这是语义错误；窗口内数据必须稳定。
- **采样边沿不清楚**：用垂直标记线 + 小三角 / 箭头；不要只靠文字说明。
- **波形错位 / 毛刺**：跳变点 X 没落在 `X0 + beat×CW` 或半拍边界上。
- **总线文字压线**：文字框高度用 16–18px，中心放在 `Y_mid`，并确保背景块在文字下方。
