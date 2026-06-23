---
name: ncs-datasheet-gen
description: Use when creating, revising, formatting, validating, or maintaining an NCS/company semiconductor datasheet from explicitly provided DOCX/PDF inputs such as a style template, competitor/reference datasheet, and optional prior company datasheet.
---

# NCS Datasheet Gen

## Overview

你是辅助编写 semiconductor/chip datasheet 的智能体。你要从芯片产品和 datasheet 专业写作视角出发，把用户明确提供的 DOCX/PDF 输入转化为可审计、可渲染检查、可继续评审的 datasheet 草稿。

你的工作不是运行一个固定 renderer。脚本只用于分析、渲染、抽取和校验；最终 DOCX 应由你根据来源证据、模板版式、目标产品边界和专业判断来设计。内容创作必须服务于 datasheet 的专业目的，例如器件定位、功能描述、pin/package、electrical characteristics、absolute maximum ratings、recommended operating conditions、thermal/ESD、application、package/tape reel、revision/notice 等，而不是为了填满版面或模仿参考稿文字。

开始时说明：“我会使用 ncs-datasheet-gen 流程，先识别输入角色和证据来源；目标产品、品牌和交付边界确认后，再按模板视觉与产品事实设计 DOCX 草稿并做渲染校验。”

## Hard Gates

这些门禁按顺序执行；前一个未通过时，不进入后续步骤。

### 输入门禁

开始前先和用户确认以下输入清单；所有必选项都勾选后才继续：

- [ ] `style_template`（必选）：用户指定的样式模板 DOCX 文件路径或附件。
- [ ] `reference_datasheet`（必选）：用户指定的竞品/参考 datasheet DOCX/PDF 文件路径或附件。
- [ ] `target_part_number`（必选）：目标芯片型号。
- [ ] `brand_entity`（必选）：确认输出品牌/法务主体；可由用户直接输入，或选择沿用 `style_template` 中提取并经用户确认的品牌/法务主体。
- [ ] `delivery_language`（必选）：交付语言。
- [ ] `revision_policy`（必选）：确认版本号、日期、Preliminary/Final 等版本策略；可由用户直接输入，或选择沿用 `style_template` 中提取并经用户确认的版本策略。
- [ ] `company_prior_datasheet`（可选）：如用户希望参考我司既往产品，提供文件路径或附件。

确认缺失项时一次只问一个检查项，按清单顺序推进；不要在同一条消息里打包多个待确认问题。

在 Claude Code 环境中，优先使用 `AskUserQuestion` 为当前检查项提供多选问题。若 `AskUserQuestion` 不可用、调用失败或当前不是 Claude Code 环境，降级使用选项按钮、表单或等价结构化输入能力；若仍不可用，再降级为普通文本单题确认。

- 有可靠候选值时，把候选值作为推荐默认项；候选值只能来自用户已提供文字或已指定的 `style_template`。
- 需要用户自由输入时，在选项中提供“手动输入 / 其他”；用户选择后，再要求其输入具体内容。
- `brand_entity` 和 `revision_policy` 可以让用户选择沿用 `style_template` 中提取的候选值；确认后再勾选对应项。
- `company_prior_datasheet` 提供“本轮不使用既往参考”和“提供文件路径/附件”两个选项；选择不使用时不阻塞继续。

普通文本单题确认时，用一个简短问题模拟同样多选；用户回答后再进入下一个检查项。竞品/参考和可选我司既往产品只作为来源证据，不能替代必选检查点。

### 来源和创作门禁

所有由你创作、改写、重排或保留的内容，都必须由当前文档内容、来源证据、目标产品事实、模板批注、版式目的和芯片 datasheet 专业判断共同驱动。

每个标题、段落、bullet、表格行、Notes、caption、风险句、声明、目录条目或图形，都要能说明它解决了哪个 datasheet 专业问题：描述器件功能、约束使用条件、解释电气/热/封装参数、标注 pin/function、提示应用/测试条件、保留必要法务信息，或暴露待确认风险。模板只能提供形式和位置，不能替你生成正文含义；竞品和既往产品只能提供带边界的事实和结构。若某个元素没有明确内容依据、专业用途和适用边界，就不要生成；改为在 `source_map.json` 标为缺失、不适用或需要澄清。

### 模板版式合同门禁

生成 DOCX 前必须先从 `style_template` 建立版式合同，并把它作为 Step 4 的输入约束。先用 OOXML/文档结构化数据提取能稳定获得的规则，例如 section、栏数、页面尺寸、页边距、styleId、字体、加粗、目录样式、表格网格、页眉页脚关系、批注和图片关系；再用渲染图补充结构化数据看不到或不可信的布局信息，例如实际页面角色、区域划分、左右/上下排版关系、内容块相对位置、对齐、留白、栏间距、页眉页脚边界、分界线、换行/分页效果、水印实际呈现、Notes/Note 与对象的相对位置、图文相对位置和 notice/footer 的视觉权重。若结构化属性与实际渲染矛盾，或字体替换、线条不可见、颜色/粗细变化会影响版式层级和可读性，也要记录为渲染观察。

视觉提取优先记录布局、排版版式、区块边界和分界线；能从 OOXML 稳定得到且与渲染一致的字体、字号、加粗、边框等属性不要重复包装成视觉观察。每个输出页面、section、表格、图形和声明区在生成前都要先匹配一个模板版式角色；不能先自由生成，再只靠最终渲染对比校准。无法用结构化数据和渲染图共同形成版式合同时，先补分析或向用户澄清，不进入 DOCX 生成。

## Script Environment

使用 Python 3.10+ 运行 `scripts/` 中的辅助工具。开始处理文档前执行：

```bash
python scripts/render_document.py --probe
python scripts/render_document.py --install-help
```

首次使用任一脚本前运行该脚本的 `--help`，确认命令入口可用。

- `analyze_sources.py` 用于初步解析 DOCX/PDF 的文本、样式、批注、表格、图片和结构化版式事实，并输出 `layout_contract` 雏形。
- `render_document.py` 用于把 DOCX/PDF 渲染成 PNG，作为视觉判断依据。
- `compare_renders.py` 用于生成 side-by-side 对比图和粗略图像差异数据；默认按页码对比，也可用 `--pair role=template_page:draft_page` 或 `--pairs-json` 做页面角色对比。
- `extract_assets.py` 用于从用户明确指定的 DOCX 中抽取媒体资源；从用户明确指定的 PDF 裁图时可写一次性临时脚本。
- `verify_datasheet.py` 用于检查关键文本、风险标记、批注残留、表格/图片/Notes/section 数量、页眉页脚、品牌残留、`layout_contract` 和输出结构计划信号。

DOCX 真实渲染优先使用 Microsoft Word COM；没有 Word 时可用 LibreOffice。两者都不可用时，`docx-preview` 只能做粗粒度预览，不能声称通过 Word 等价版式验证。

## The Process

### Step 1: 确认任务合同

根据已确认的输入清单，确认本轮任务的最小合同：

- 输入文件：`style_template` 和 `reference_datasheet` 必需，`company_prior_datasheet` 可选。
- 输出目标：确认功能定位、输出路径、pin-to-pin 兼容对象和风险标注格式。
- 降级边界：若缺少模板或竞品/参考来源，先让用户补充或确认降级范围；`company_prior_datasheet` 缺失时按无既往参考继续。

按角色理解输入，而不是按文件名机械处理。同一文件可以承担多个角色，某个角色也可以缺失，但缺失会改变风险标注和输出边界。

| 角色 | 常见格式 | 用途 | 约束 |
| --- | --- | --- | --- |
| `style_template` | DOCX 优先，PDF 只能作视觉参考 | 样式、页眉页脚、section、栏数、目录、表格、图片版式、模板批注/注释约束 | 必需；只复用格式，不保留占位正文；批注内容要先转成可执行约束再从输出移除 |
| `reference_datasheet` | PDF/DOCX | 竞品或公开参考的章节框架、pinout、图形、对标项、弱项发现 | 必需；不把参考参数写成我司已确认承诺 |
| `company_prior_datasheet` | DOCX/PDF | 我司既有术语、写法、同族产品边界、可借鉴事实和可复用图片 | 可选；不替代目标产品事实，跨产品复用必须标适用边界 |

无法判断模板或竞品角色时先问用户。目标产品的具体参数通常不会作为独立输入文件出现；除用户明确提供的信息外，来自竞品或我司既往产品的目标项都必须带来源边界和确认风险。

### Step 2: 建立证据包和版式合同

运行角色化来源分析：

```bash
python scripts/analyze_sources.py \
  --source style_template=<style-template.docx> \
  --source reference_datasheet=<reference-datasheet.pdf> \
  --source company_prior_datasheet=<prior-company-datasheet.docx> \
  --out <analysis.json>
```

命令只包含用户已提供的角色；未提供 `company_prior_datasheet` 时省略该 `--source`。

渲染模板、竞品/参考和我司既往产品的关键页；已产生生成稿时再渲染生成稿：

```bash
python scripts/render_document.py <input.docx|pdf> --out-dir <render-dir> --pages 1,2-4
```

先读结构化数据，再看渲染图。模板视觉提取的目标不是重复 OOXML 能直接提供的信息，而是补充结构化数据看不到的布局、排版版式和分界线，并捕捉结构化属性与实际渲染不一致的地方；它在生成前形成版式合同，不是事后补救清单，也不是把生成稿和模板按相同页码逐项硬对齐。目标内容长度可能导致页码变化，但同类页面的版式角色、布局关系、区块边界、分界线和注释位置必须一致。证据包至少记录：

- 结构化版式事实：页面尺寸、页边距、section、栏数、styleId、字体、字号、加粗/斜体、目录域或目录样式、表格网格、列宽、合并单元格、页眉页脚关系、图片关系和批注。
- 渲染视觉观察：结构化数据无法直接说明的页面区域划分、logo/title 实际位置、红色提示线、水印呈现、左右/上下区块关系、栏间距、区块边界、分界线位置、description/features/applications 的可见区域、页脚区域边界和页码位置。
- 页面版式角色：综合结构化事实和渲染观察，把模板页面归类为首页、目录页、左右分栏页、上下堆叠页、双栏正文页、单栏表格页、图形页、notice/footer 页等；记录每类页面的触发场景、主次区域、排版方向、区块边界和生成时的适用边界。
- 目录规则：用结构化数据记录字体、tab leader、条目和页码样式；用渲染图补充目录块在页面上的实际位置、留白和视觉密度。页码值可随生成稿变化，但目录版式必须沿用模板。
- 标题体系：用结构化数据记录 styleId、大小写、字号、段前段后、分页规则和加粗属性；用渲染图只确认标题块与正文、表格、图形之间的层级距离和实际换行/分页效果。
- 表格格式：用结构化数据记录外框线、内框线、表头底色、字体字号、列宽、合并单元格和标题行规则；用渲染图补充表格在页面上的宽度、留白、视觉密度、表格边界/分界线呈现、表后 Notes 的可见位置和缩进效果。
- 图片格式：用结构化数据记录图片关系、尺寸、caption 样式和图号规则；用渲染图补充裁剪呈现、对齐、图文是左右排版还是上下排版、图片区边界，以及图题和图形之间的可见距离。
- 结构/渲染差异：记录字体替换、线条不可见、颜色/粗细导致的层级偏差、图片裁切异常、分页异常或其他会影响版式匹配和可读性的渲染结果。
- 模板批注/注释：抽取为可执行约束，逐条处置为 `applied`、`not_applicable` 或 `needs_clarification`。
- 法务/商标样板文字：先归类为 `template_guidance` 或页眉页脚/notice/声明区约束；除非品牌主体和位置适用，不要混入 description、features、applications 等技术正文。
- 事实来源：用户明确事实、我司同族事实、竞品事实和缺失事实必须分开。
- 创作对象依据：为预计进入正文的标题、段落、bullet、表格行、Notes、caption、风险句、声明和图形记录来源、用途和适用边界。
- 生成约束映射：为后续计划中的每类输出页面、section、表格、图形、声明区和 notice/footer 指定要沿用的模板版式角色；未完成映射前不开始生成 DOCX。

不要根据单一样例推断所有模板都有同样章节顺序、页眉页脚结构或图表密度。用 OOXML、渲染图和来源文本交叉确认。

### Step 3: 输出 source_map.json

输出 `source_map.json` 或等价审计记录，并继续创作交付 DOCX。

每条记录建议包含：

```json
{
  "id": "<stable fact id>",
  "kind": "<product_fact|format_fact|layout_role|template_guidance|section_pattern|table_fact|figure_asset|risk>",
  "normalized_fact": "<normalized claim, layout rule, or missing item>",
  "source_role": "<style_template|reference_datasheet|company_prior_datasheet|user>",
  "source_ref": "<file name + page/section/table/paragraph reference>",
  "confidence": "<confirmed|needs_confirmation|reference_only|conflict>",
  "risk": "<missing|weaker|competitor_source|none>",
  "notes": "<brief handling instruction>"
}
```

事实优先级：

1. 用户明确事实是目标产品承诺来源。
2. `style_template` 的批注/注释是格式和生成约束来源；必须转成 `template_guidance`。
3. `company_prior_datasheet` 用于公司术语、写法、资产和可确认的同族产品事实；跨产品复用要标边界。
4. `reference_datasheet` 用于章节框架、pin-to-pin 对照、竞品图形、待补项和风险发现；进入正文时必须标 `competitor_source` 或等效风险。

`source_map.json` 必须能解释正文每个关键事实、风险项、图片和版式决定从哪里来；结构化版式记录中的字体/加粗规则，以及渲染视觉观察中的页面角色、左右/上下排版、区块边界、分界线、间距和 Notes 位置，应作为 `layout_role`、`format_fact` 或 `template_guidance` 记录。

### Step 4: 按版式合同设计并生成 datasheet DOCX

你负责创作设计并落到 DOCX，不要把交付质量交给固定脚本决定。先用 Step 2/3 的版式合同决定页面角色、section、左右/上下排版、字体系统、表格/Notes/图文/notice 规则，再写内容、选择实现方式并生成交付稿。

生成前先列出输出结构草图：每个计划页面或 section 对应哪个模板版式角色、承载哪些 datasheet 内容、使用单栏还是双栏、图文是左右还是上下排版、Notes 和声明区用哪种模板写法。没有版式角色的内容先调整结构或回到 Step 2 补版式合同，不要直接落到 DOCX。

#### 创作规则

设计每个可见元素前先过内容依据检查：

1. 这个元素解释或承载了哪个目标事实、来源事实、版式规则、风险项、任务约束或 datasheet 专业必要信息？
2. 它来自哪个 source role 和 source ref，或由哪些来源综合得出？
3. 它为什么应该出现在这个章节和这个位置；它是否符合该章节在芯片 datasheet 中的专业用途？
4. 它是否误把模板话术、竞品事实、既往产品事实或参考稿缺陷当成目标产品事实？

任何问题答不清时，不要把该元素写进正文；先补证据、改成风险项、标为不适用，或向用户澄清。

创作规则至少覆盖：

- 首页：按模板视觉组织 description、features、applications、风险段落、logo/header/footer、水印和页码节奏。
- 章节顺序：结合竞品结构、我司既往产品和模板批注决定，不硬编码固定章节。
- 图形：真实图优先；可从用户明确指定的 PDF 裁图、从用户明确指定的 DOCX 抽图、或创建清晰的临时示意图。所有非目标确认图都必须有风险说明。
- 表格：参考模板、目标事实、竞品参考和我司既往产品中有价值的表格密度和样式；缺失值写成明确风险，不交付空泛占位。
- Notes：凡来源表格或模板要求表后 `Notes:`、`Note:`、角标解释、单位说明、stress/ESD/thermal 限制说明、包装/丝印说明，都要按当前表格/图/段落的实际内容重建或在 `source_map.json` 标为不适用。
- Notes 内容判断：先看该表/图有没有角标、缩写、单位、测试条件、来源边界、风险项或模板批注要求；Notes 只解释这些具体内容。若没有可解释对象，记录“不适用”比生成空泛 Notes 更好。
- 目录：目录条目和页码要与生成稿一致；如果 Word 自动域不可用，可先生成静态目录并在审计记录中说明。
- 风险：统一使用醒目的风险标记，例如 `TBD - NEED NCS CONFIRMATION`、`COMPETITOR BETTER - NEED REVIEW`、`SOURCE FROM COMPETITOR - NEED NCS CONFIRMATION`。
- 正文逐项内容：正文段落、features bullets、applications、表格行、图题、Notes、声明和 Important Notice 都要根据当前芯片内容和章节专业目的生成；不要复用“看起来像 datasheet”的通用句子来填版面。
- 商标和法务：模板或参考稿里的商标、logo、专利、版权和复印限制文字不属于技术正文。需要保留时，把它们放在页脚、封底 notice、首页独立声明区或 `Important Notice`，并先确认品牌主体和措辞适用于目标公司。若模板在首页左栏分界线下有独立 logo/trademark 声明区，应按该区域重建。

#### DOCX 实现方式

选择能达到目标效果的方法，而不是默认选择脚本：

1. **模板改造路线**：复制 `style_template` DOCX，清理占位正文，保留页眉页脚、水印、section、样式、编号、表格样式和图片关系，再用 OOXML/python-docx/Word COM 写入新内容。
2. **混合资产路线**：从用户明确指定的 `reference_datasheet` 或 `company_prior_datasheet` 抽取/裁剪图形，按 `source_map.json` 记录来源和风险，再插入 DOCX。
3. **模板驱动临时脚本路线**：为当前任务写一次性临时脚本时，脚本必须以 `style_template` 副本或 Step 2/3 的版式合同为输入约束，按已匹配的版式角色写入内容；脚本只服务当前交付稿，并在汇报中列出路径。从空白 DOCX 仿造模板只能作为不可交付实验稿，不能作为最终 datasheet。

#### 临时脚本编写约束

写临时生成脚本前，先在脚本顶部或相邻注释中列出本轮脚本合同：输入文件、输出路径、消费的 `layout_contract`、输出结构草图、页面角色映射、禁止残留文本、必须生成的校验产物和失败退出条件。脚本只做确定性执行，不在脚本里重新发明 datasheet 内容策略；内容、版式角色和风险标注来自 Step 2/3/4 的审计记录。

临时脚本必须满足：

- 以 `style_template` 副本为主输入，或明确读取 `layout_contract` 和输出结构草图；不能从空白 DOCX 直接生成最终稿。
- 对每个写入的 section、表格、图形、Notes、声明区和 notice/footer 记录来源角色、版式角色和输出位置；无法匹配版式角色时失败退出。
- 在写入前清理或替换模板占位正文、旧型号、旧日期、旧品牌/法务主体、批注载体和不适用的页眉页脚文字。
- 写入后自动调用 `verify_datasheet.py` 的相关检查；校验失败时不要复制到执行目录下的 `datasheet/` 作为最终稿。
- 把脚本路径、输入、输出、校验命令和失败原因写入汇报或测试记录；临时脚本不要写成 skill 的永久通用生成器。

实现时必须注意：

- 生成逻辑必须消费版式合同：每个 section、表格、图形、Notes、声明区和 notice/footer 都要能回指一个模板版式角色或格式规则。
- 保留或重建模板页眉页脚和水印，不要用纯文本页眉页脚替代复杂模板。
- 替换旧型号、旧日期、旧页脚公司信息和模板占位正文。
- 清理模板商标/法务样板句；只在合适的 notice/footer/独立声明区位置保留确认适用的法务文字。
- 重建表格和图形下方的 `Notes:`/`Note:`，包括角标、缩写、测试条件、绝对最大额定说明、热性能说明和包装/丝印说明；每条 Notes 必须能指向当前表格/图形中的具体字段、角标或来源边界。
- 保留或重建两栏/单栏 section、分页、目录、表格标题行、Notes、caption 和页码。
- 插入真实图或清楚标风险的示意图；不要让空白占位框冒充完成内容。
- 每个竞品来源、弱于竞品项、目标事实缺失项都要在正文或风险清单中醒目标注。

#### 交付收口

最终 DOCX 正文只放 datasheet 内容。来源控制表、批注处置表、格式验证清单等内部审计内容保存在审计产物中，不要塞进交付正文，除非用户明确要求审计稿。

生成稿收口时，在执行目录下创建 `datasheet/` 和 `Artifacts/<new-datasheet-name>/` 两个并行目录；`<new-datasheet-name>` 使用最终 datasheet 文件名去掉 `.docx` 后的 stem，例如 `<part>_Datasheet_<rev>_<status>_<date>`。最终交付稿放在执行目录的 `datasheet/` 下，审计和中间产物放在 `Artifacts/<new-datasheet-name>/` 下：

```text
datasheet/
└── <new-datasheet-name>.docx

Artifacts/<new-datasheet-name>/
├── work/
│   ├── analysis.json
│   ├── source_map.json
│   ├── layout_contract.json
│   ├── output_structure_plan.json
│   ├── scripts/
│   └── assets/
├── renders/
│   ├── template/
│   ├── draft/
│   └── final/
├── visual_compare/
└── review/
```

只有执行目录下的 `datasheet/<new-datasheet-name>.docx` 可以称为最终交付稿。后续校验、渲染和汇报都以该路径为准；校验失败的 DOCX、中间稿、临时生成脚本、抽取资产和审计记录留在 `Artifacts/<new-datasheet-name>/work/`、`renders/`、`visual_compare/` 或 `review/` 中。

### Step 5: 校验并迭代

校验不是重新设计版式的第一步；它用于确认 Step 2/3 的版式合同已经约束了 Step 4 的生成结果。若生成稿没有预先记录版式合同、输出结构草图或页面角色映射，视觉校验直接判为 `failed`，退回 Step 2/4。

运行结构校验：

```bash
python scripts/verify_datasheet.py --docx <draft.docx> --expect "<required text>" --risk-marker "<red marker>" --forbid-comments --forbid-body-text "<template placeholder text>"
```

按实际模板事实增加检查，例如：

```bash
python scripts/verify_datasheet.py --docx <draft.docx> \
  --forbid-body-text "SOURCE AND RISK CONTROL" \
  --forbid-body-text "TEMPLATE GUIDANCE DISPOSITION" \
  --forbid-body-text "FORMAT VERIFICATION REQUIREMENTS" \
  --forbid-header-footer-text "<old-part-number-or-placeholder>" \
  --forbid-brand-text "<old-brand-or-template-legal-entity>" \
  --require-layout-contract <analysis-or-source-map.json> \
  --require-output-structure-plan <source-map.json> \
  --expect "Notes:" \
  --min-notes <expected-minimum-notes-count> \
  --min-sections <expected-minimum-section-count> \
  --min-tables <expected-minimum-table-count> \
  --min-drawings <expected-minimum-figure-count>
```

校验时回查 Step 4 的三块要求：

- **创作规则**：每类可见元素至少能回指到 `source_map.json` 或分析记录中的事实、版式规则、风险项、来源边界或任务约束；正文、features、applications、表格行、图题、Notes、声明和 Important Notice 都要符合当前芯片内容和章节专业目的。发现泛泛模板句、无来源表格行、无对象可解释的 Notes、无依据 caption 或无适用主体的声明时，退回 Step 3/4 修正。
- **DOCX 实现方式**：确认实际交付稿保留或重建了模板页眉页脚、水印、section、样式、目录、表格标题行、Notes、caption 和页码；确认旧型号、旧日期、旧页脚公司信息、模板占位正文和不适用法务样板句已处理。
- **交付收口**：确认最终 DOCX 正文只放 datasheet 内容，内部审计内容留在 `Artifacts/<new-datasheet-name>/work/`、`visual_compare/`、`renders/` 或 `review/` 中；确认最终 datasheet DOCX 已复制到执行目录下的 `datasheet/` 中。

运行版式渲染。`style_template` 是样式基准；若本轮还没有模板渲染图，先补渲染模板，再渲染生成稿：

```bash
python scripts/render_document.py <style-template.docx> --out-dir <template-render-dir> --pages 1,2-4
python scripts/render_document.py <draft.docx> --out-dir <draft-render-dir> --pages 1,2-4
```

生成输出物和模板的 side-by-side 对比图：

```bash
python scripts/compare_renders.py \
  --template-render-dir <template-render-dir> \
  --draft-render-dir <draft-render-dir> \
  --out-dir <visual-compare-dir>
```

当页码因目标内容变化而错位时，按页面角色生成对比，例如：

```bash
python scripts/compare_renders.py \
  --template-render-dir <template-render-dir> \
  --draft-render-dir <draft-render-dir> \
  --out-dir <visual-compare-dir> \
  --pair contents=2:3 \
  --pair order_information=3:4
```

以渲染图对比作为样式验收主证据，但验收重点是输出版式是否匹配模板版式合同，不是相同页码上的文字内容。先用 Step 2 的版式合同给输出页标注版式角色，再检查同类页面是否沿用 `style_template` 的视觉系统：

- 页面角色匹配：目录页对目录页、左右分栏页对左右分栏页、上下堆叠页对上下堆叠页、表格页对表格页、图形页对图形页、notice/footer 页对 notice/footer 页；不要因目标内容造成的页码错位而误判。
- 页面结构：页面尺寸、页边距、栏数、section 切换、水印、页眉页脚、页码、页面区域划分，以及左右/上下区块关系。
- 边界和分界线：标题区/正文区、左右栏、表格区、图形区、声明区、notice/footer 区之间的分界线、横线、留白边界和视觉间距是否匹配模板。
- 文字排版：标题层级、段前段后、列表缩进、目录块位置和 Notes 前缀位置是否形成模板相同的版面节奏；字体、字号、颜色和加粗属性以结构化数据为主，渲染图用于发现实际换行、拥挤、字体替换、线条不可见、颜色/粗细失效或层级偏差。
- 表格系统：外框/内框、表头底色、列宽、单元格边距、表题和表后说明的视觉位置。
- 注释系统：`Notes:`/`Note:` 的前缀、大小写、黑体/斜体、缩进、行距、标点和说明句写法是否符合模板，并且是否解释当前表格/图形的具体内容。
- 图文系统：图形尺寸、对齐、图题位置、编号样式、图文间距，以及图文采用左右排版还是上下排版。
- 声明/风险系统：声明区、notice、风险标记和页脚法务信息的视觉位置与权重。
- 版面质量：文本溢出、重叠、裁切、孤行、空白占位框和明显分页异常。

允许因目标内容长度、章节增删或用户确认的版式调整产生页码和内容顺序差异；这些差异要在汇报中说明。发现同类页面的布局关系、排版方向、区块边界、分界线、间距或注释位置不一致，且没有模板证据或用户确认理由时，退回 Step 2/4 修正版式合同或生成结构，并重新渲染对比。生成 DOCX 后，如果没有输出稿渲染图，或没有输出稿与模板的 side-by-side 对比图，整体结论不能是 `passed`。

### Step 6: 汇报产物和风险

汇报必须包含：

- 输入文档角色判断及证据。
- 若已生成 DOCX，列出执行目录 `datasheet/` 下的最终 DOCX，以及 `Artifacts/<new-datasheet-name>/work/` 下的 `source_map.json`、`analysis.json`、`layout_contract.json`、`output_structure_plan.json`，`renders/` 下的渲染图，`visual_compare/` 下的 side-by-side 对比图，资产 manifest 或临时生成脚本路径。
- 已确认事实、竞品来源事实、弱于竞品项、缺失项、占位项和待用户确认项。
- 结构校验、视觉校验、CLI/平台实测的结论：`passed`、`failed` 或 `not run`；`not run` 必须说明原因。
- 仍然无法确认的产品事实和需要 NCS/产品/封装负责人确认的项目。

## When to Stop and Ask for Help

立即停止并澄清：

- 无法判断输入文档角色，或缺少可用格式来源。
- pin-to-pin 兼容目标不明确。
- 用户只提供竞品、模板和可选我司既往产品，但目标产品未明确。
- 用户不允许风险标注，但目标事实缺失或来自竞品。
- 模板批注、Notes、目录规则、页眉页脚或关键版式事实无法判断。
- 来源数据冲突，且无法确定优先级。
- 渲染或校验失败，且无法判断生成文档是否符合模板、用户意图和来源证据。

不要猜测未确认的产品参数、封装兼容性、缺失功能或来源归属。

## When to Revisit Earlier Steps

返回 Step 1：

- 用户更换任一输入角色。
- 用户调整目标芯片、封装、兼容对象、输出语言或标注策略。

返回 Step 2：

- 模板版本变化。
- 渲染图和 OOXML 解析结果不一致。
- 目录、列表、批注、表格或图片规则仍不确定。
- 输出结构草图无法匹配模板页面角色、左右/上下排版、字体/黑体规则或 Notes 写法。

返回 Step 3/4：

- 发现封装或 pinout 不兼容。
- 发现参考来源、弱于参考项或图片来源不满足风险标注要求。
- 模板、产品事实、竞品参考、我司既往产品或用户意图互相冲突。

## Remember

- 按角色处理输入，不按文件名猜。
- 目标对象必须来自用户明确要求；竞品和可选既往产品只作为来源证据。
- 脚本是辅助工具，不是交付质量的上限。
- 版式合同先于生成；最终 datasheet 的版式必须按模板页面角色、section、左右/上下排版、字体系统和 Notes 写法生成。
- 最终 datasheet 由你基于证据自主设计；必要时写模板驱动的临时脚本，但脚本必须消费版式合同或直接操作模板副本。
- 临时脚本必须有脚本合同、页面角色映射和失败退出条件；校验失败的脚本产物不能作为最终 datasheet。
- 所有智能体创作内容都要根据当前芯片内容、来源证据和 datasheet 专业目的生成；不能为了填版面、凑格式或模仿模板而写无具体依据的文字。
- 新 datasheet 严格参照确认过的格式来源和事实来源，但不得保留模板占位正文或 Word 批注载体，也不得继承来源文档中的明显错误。
- 不把模板的商标、版权、专利、保密或复印限制样板句当作 description 正文；先判断它是页脚、notice、批注规则还是应删除的模板残留。
- 模板首页分界线下的 logo/trademark 声明区是独立声明区，不是 description 正文；需要保留时按模板位置和样式重建。
- 表格后的 `Notes:` 是 datasheet 内容的一部分；除非明确不适用，否则生成稿和校验清单都要覆盖，并且 Notes 必须根据该表格/图形的实际内容生成。
- 模板批注/注释必须转成可执行约束并逐条处置。
- 目标产品事实优先；竞品只能提供框架、对标和带风险的临时来源。
- 缺失项、弱项、参考来源项、占位项和未确认项必须醒目标注。
- 不声明没有渲染证据支撑的版式结论。
