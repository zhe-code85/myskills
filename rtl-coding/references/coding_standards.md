# RTL 编码规范参考

## Verilog 编码规范

### 文件组织
- 每个模块一个文件，文件名与模块名一致
- 文件扩展名优先使用 `.v`
- 公共定义、宏、局部参数可放在 `.vh` 头文件中
- 模块端口声明统一使用 ANSI 风格：在 `module` 的参数/端口列表中直接声明方向、位宽和类型；不要使用非 ANSI 风格的“端口名列表 + 后置 `input`/`output`/`inout` 声明”
- 信号声明一行只声明一个信号，不在单行内连续声明多个 `wire` 或 `reg`

### 命名规范
- 模块名：`snake_case`（如 `data_path`、`ctrl_reg`）
- 信号名：`snake_case`（如 `data_in_valid`、`fifo_full`）
- 参数名：`UPPER_SNAKE_CASE`（如 `DATA_WIDTH`、`FIFO_DEPTH`）
- 时钟：`clk` 或 `clk_<domain>`
- 复位：`rst_n`（低有效）或 `rst`（高有效）
- 现态寄存器命名不做限定；其 next-state / next-data 组合信号必须是「完整现态寄存器名 + `_comb`」，不得对寄存器名做任何删改后再加 `_comb`

### 注释规则
- 注释用于说明模块意图、接口语义、功能块边界、非显然实现选择和关键假设。
- 每个端口必须有注释，说明信号用途；控制/握手/状态类端口还应说明有效条件、方向语义或背压关系。
- 每个由模块设计输入定义的功能点，都必须能在 RTL 中定位到对应注释；注释应写在实现该功能的功能块、关键状态、关键组合求值或关键时序更新附近。
- 每个主要功能块前必须有注释，说明该块负责的功能、输入依赖和输出结果。功能块包括 port list、参数/本地参数区、状态机、握手/背压、仲裁、buffer/FIFO、pipeline stage、寄存器读写、异常/错误处理、CBB/IP 例化、关键组合求值和关键时序更新。
- 关键内部信号、寄存器、状态枚举和 `*_comb` next-state 信号应有注释，说明它们承载的设计语义；临时中间线网可不注释。
- 复位行为、非法输入处理、边界条件、位宽截断/扩展、跨时钟域、CBB/IP wrapper 参数适配等容易误读的位置必须加注释。
- 注释必须描述设计意图或协议语义，不写逐行旁白式注释，也不要用注释重复代码字面含义。

### 编码规则
- 输出端口必须使用寄存器时序电路输出；每个 output 端口必须有对应的 `reg` 信号和时序更新块。
- 状态机的状态转移（next-state）组合逻辑必须以当前状态寄存器为选择条件使用 `case` 语句组织；每个状态分支内可按输入条件使用 `if` / `else` 决定 next-state 取值，但不要用多层 `if-else` 嵌套替代顶层状态 `case`。
- 逻辑实现统一采用两段式
- 时序逻辑使用 `always @(posedge clk or negedge rst_n)` 或项目约定的同步复位写法
- 可综合模块默认使用 Verilog 语法；除非项目明确约定使用 SystemVerilog 子集，否则不要引入 SystemVerilog 写法，以避免误用验证或仿真专用语法
- `#delay` 不用于定义逻辑功能行为；如需使用，仅作为仿真辅助延时
- `initial` 默认不用来描述上电行为；FPGA 流程可按工具约定使用，ASIC 流程应使用 reset 或明确的初始化机制
- 异步复位分支只赋常量
- 不在时序 `always` 块中使用阻塞赋值（`=`）
- 不在组合 `always @(*)` 块中使用非阻塞赋值（`<=`）
- 同一信号保持单一驱动源
- 每个 `reg` 信号的时序赋值单独占一个 `always` 块；不要在同一个时序块中更新多个 `reg`
- 位宽匹配：运算和赋值两侧位宽应一致
- 宽度、截断、拼接和符号扩展显式处理，不依赖工具隐式推断
- 需要符号扩展时显式使用 `$signed()`
- 避免使用 `/` 直接除变量
- 组合逻辑中的控制分支应完整覆盖目标信号的赋值，避免引入非预期 latch
- 每个 `always @(*)` 块只描述一个目标信号的组合逻辑；不同信号分别拆成独立块
- 跨时钟域逻辑使用专用同步器、异步 FIFO 或明确的 CDC 模块，不写隐藏的 CDC 逻辑

### 两段式定义

- 两段式由时序块和组合块组成
- 时序块负责寄存器在时钟驱动下的更新和异步复位
- 组合块负责根据当前状态和输入计算下一状态及组合输出
- 简单组合逻辑可使用连续赋值，复杂组合逻辑使用 `always @(*)`

#### 两段式示例

反例：同一功能的一段式写法，包含两种违规：

- 在时序块中同时完成 next-state 求值和寄存器更新。
- 同一个时序 `always` 块中更新多个 `reg`。

```verilog
reg cnt_div2;
reg [2:0] cnt_10;

// 一段式写法：时序块中同时完成 next-state 求值和寄存器更新
always @(posedge clk or posedge rst) begin
    if (rst) begin
        cnt_div2 <= 1'b0;
        cnt_10 <= 3'd0;
    end else begin
        cnt_div2 <= ~cnt_div2;
        if (cnt_10 == 3'd4) begin
            cnt_10 <= 3'd0;
        end else begin
            cnt_10 <= cnt_10 + 3'd1;
        end
    end
end
```

同一功能的两段式写法：

```verilog
reg cnt_div2;
wire cnt_div2_comb;

reg [2:0] cnt_10;
reg [2:0] cnt_10_comb;

// cnt_div2 的组合逻辑块：简单 next-state 使用连续赋值
assign cnt_div2_comb = ~cnt_div2;

// cnt_10 的组合逻辑块：复杂 next-state 使用 always @(*)
always @(*) begin
    cnt_10_comb = cnt_10 + 3'd1;
    if (cnt_10 == 3'd4) begin
        cnt_10_comb = 3'd0;
    end
end

// cnt_div2 的时序块：只负责 cnt_div2 更新和异步复位
always @(posedge clk or posedge rst) begin
    if (rst) begin
        cnt_div2 <= 1'b0;
    end else begin
        cnt_div2 <= cnt_div2_comb;
    end
end

// cnt_10 的时序块：只负责 cnt_10 更新和异步复位
always @(posedge clk or posedge rst) begin
    if (rst) begin
        cnt_10 <= 3'd0;
    end else begin
        cnt_10 <= cnt_10_comb;
    end
end
```

### 交付前最低合规检查项

以下清单供 `rtl-coding` 在编码完成前 review 时使用，并写入 `<module_name>/review_report.md` 的 coding standards 结论；它不替代全文，只用于保证交付前可追溯：

- 模块文件位于 `<module_name>/*.v` 或 `<module_name>/*.sv`，模块名与主文件名一致
- 模块端口使用 ANSI 风格声明
- 输出端口都使用寄存器时序电路输出，每个 output 端口都有对应的 `reg` 信号和时序更新块
- 状态机的状态转移（next-state）组合逻辑以当前状态寄存器为选择条件使用顶层 `case` 语句组织；状态分支内可按输入条件使用 `if` / `else` 决定 next-state 取值
- 每个端口都有说明用途和协议语义的注释
- 每个由模块设计输入定义的功能点，都能在 RTL 中定位到对应注释
- 每个主要功能块前都有说明职责、输入依赖和输出结果的注释
- 每个声明行只包含一个 `wire` / `reg` / 等价声明项
- 时序逻辑与组合求值采用两段式
- 每个 `reg` 信号的时序赋值单独占一个 `always` 块，不在同一个时序块中更新多个 `reg`
- next-state / 组合求值信号命名为「完整现态寄存器名 + `_comb`」，未对寄存器名删改后再加后缀
- 时序块使用非阻塞赋值，组合块使用阻塞赋值
- 异步复位分支只赋常量
- 每个 `always @(*)` 块只描述一个目标信号，并完整覆盖该目标信号赋值，避免 latch
- 同一信号只有一个驱动源
- 运算和赋值两侧位宽匹配；有意截断或扩展时显式写明
- 不手写组合门控时钟
- 不写隐藏 CDC 逻辑
- CBB/IP 复用路径与输入准备度检查记录一致
- 只记录真实执行过的 lint、静态检查、仿真或附加自检；未执行项不得写成已通过
