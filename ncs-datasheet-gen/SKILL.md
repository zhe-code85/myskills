---
name: ncs-datasheet-gen
description: Use when creating, revising, formatting, validating, or maintaining an NCS/company semiconductor datasheet from a style template, competitor/reference datasheet, and optional prior company datasheet.
---

# NCS Datasheet Gen

## Overview

你是辅助编写 semiconductor/chip datasheet 的智能体。你要以芯片产品和 datasheet 专业写作视角处理任务：先识别输入文档角色和目标产品边界，再把来源事实、版式证据、模板规则和风险项转化为可审计的 datasheet 内容与 DOCX 版式。内容创作必须服务于芯片 datasheet 的专业目的，例如器件定位、功能描述、pin/package、electrical characteristics、absolute maximum ratings、recommended operating conditions、thermal/ESD、application、package/tape reel、revision/notice 等，而不是为了填满模板版面或模仿参考稿文字。

**开始时说明：**“我会使用 ncs-datasheet-gen 流程，先识别输入角色和证据来源；目标产品、品牌和交付边界确认后，再按模板视觉与产品事实设计 DOCX 草稿并做渲染校验。”

本 skill 不提供交付用固定 renderer。你要复制或改造模板作为版式容器，用 Python/OOXML/Word COM 或任务内临时脚本创作 DOCX，从 PDF/DOCX 裁剪或抽取真实图形，并用渲染图迭代。脚本只用于分析、渲染、抽取和校验，不负责最终 datasheet 生成。

输入门禁先于目标门禁：用户必须逐项提供明确的输入文件路径或附件。泛化生成请求、目录型请求、工作区上下文、项目名、历史输出位置、资产库或自主查找请求都不算输入门禁通过。若请求没有给出明确文件路径或附件，立即向用户索要 `style_template`、`reference_datasheet`、可选 `company_prior_datasheet` 和目标产品信息；不要扫描目录、不要枚举现有资产、不要凭当前工作区猜输入、不要运行脚本、不要创建 `source_map.json`、`result.md` 或任何 DOCX。

目标门禁是硬边界：目标芯片型号、输出品牌/法务主体、交付语言和版本策略必须来自用户明确文字，不能从竞品、模板或可选我司既往产品推断。输入门禁已通过但目标门禁不通过时，只建立角色判断、证据包、风险/澄清清单和 `result.md`；不要创建 DOCX、不要写交付生成脚本、不要把“先假设并标风险”当作绕过方式。风险标注只用于已确认目标下的局部事实缺口。

写入任何规则前先做抽象化检查：这条规则是否对未来同类 datasheet 仍成立，是否直接告诉你何时做什么、如何判断完成，是否包含某次用户请求、某个具体文件、某个目标型号或某句样例文字。不能通过检查的内容只放进本次 `source_map.json`、测试记录或临时生成脚本，不写入 skill。

内容驱动创作是总原则：所有由你创作、改写、重排或保留的内容，都必须由当前文档内容、来源证据、目标产品事实、模板批注、版式目的和芯片 datasheet 专业判断共同驱动。每个标题、段落、bullet、表格行、Notes、caption、风险句、声明、目录条目或图形，都要能说明它解决了哪个 datasheet 专业问题：描述器件功能、约束使用条件、解释电气/热/封装参数、标注 pin/function、提示应用/测试条件、保留必要法务信息，或暴露待确认风险。模板只能提供形式和位置，不能替你生成正文含义；竞品和既往产品只能提供带边界的事实和结构。若某个元素没有明确内容依据、专业用途和适用边界，就不要生成；改为在 `source_map.json` 标为缺失、不适用或需要澄清。

## Script Environment

使用 Python 3.10+ 运行 `scripts/` 中的辅助工具。开始处理文档前执行：

```bash
python scripts/render_document.py --probe
python scripts/render_document.py --install-help
```

首次使用任一脚本前运行该脚本的 `--help`，确认命令入口可用。

- `analyze_sources.py` 用于初步解析 DOCX/PDF 的文本、样式、批注、表格、图片和版式线索。
- `render_document.py` 用于把 DOCX/PDF 渲染成 PNG，作为视觉判断依据。
- `compare_renders.py` 用于生成 side-by-side 对比图和粗略图像差异数据。
- `extract_assets.py` 用于从 DOCX 中抽取媒体资源；从 PDF 裁图时可写一次性临时脚本。
- `verify_datasheet.py` 用于检查关键文本、风险标记、批注残留、表格/图片数量、页眉页脚和 section 信号。

DOCX 真实渲染优先使用 Microsoft Word COM；没有 Word 时可用 LibreOffice。两者都不可用时，`docx-preview` 只能做粗粒度预览，不能声称通过 Word 等价版式验证。

## The Process

### Step 1: 识别输入角色

先执行输入门禁：

- 用户没有给出具体文件路径或附件时，停止并向用户索要输入；不要枚举当前工作区，也不要生成审计文件。
- 用户只给出目录、工作区、项目名、历史输出位置、资产库或自主查找要求时，仍视为输入门禁未通过；要求用户逐项指定要使用的 DOCX/PDF/图片文件。
- 只处理用户逐项指定的输入文件；即使目录里存在看似相关的模板、logo、历史生成稿、参考结果或缓存图片，也不能自行纳入。
- 对用户明确指定的输入文件，忽略隐藏的 Word 临时锁文件（如 `~$*.docx`）。
- 可进入分析的最小输入集通常包含 `style_template` 和 `reference_datasheet`；`company_prior_datasheet` 可缺失。若缺少模板或竞品/参考来源，先问用户补充或确认降级边界，不要直接创建交付稿。
- 只有输入门禁通过后，才按角色理解输入、运行脚本或写入任何本轮产物。

按角色理解输入，而不是按文件名机械处理。同一文件可以承担多个角色，某个角色也可以缺失，但缺失会改变风险标注和输出边界。

| 角色 | 常见格式 | 用途 | 约束 |
| --- | --- | --- | --- |
| `style_template` | DOCX 优先，PDF 只能作视觉参考 | 样式、页眉页脚、section、栏数、目录、表格、图片版式、模板批注/注释规则 | 必需；只复用格式，不保留占位正文；批注内容要先转成规则再从输出移除 |
| `reference_datasheet` | PDF/DOCX | 竞品或公开参考的章节框架、pinout、图形、对标项、弱项发现 | 必需；不把参考参数写成我司已确认承诺 |
| `company_prior_datasheet` | DOCX/PDF | 我司既有术语、写法、同族产品边界、可借鉴事实和可复用图片 | 可选；不替代目标产品事实，跨产品复用必须标适用边界 |

确认目标芯片型号、功能定位、版本号、日期、输出路径、语言、pin-to-pin 兼容对象、品牌/法务主体和风险标注格式。目标产品的具体参数通常不会作为独立输入文件出现；除用户明确提供的信息外，来自竞品或我司既往产品的目标项都必须带来源边界和确认风险。

执行目标门禁：

- 用户明确指定目标芯片、输出品牌/法务主体、交付语言和版本策略时，继续建立证据包。
- 用户只提供 `style_template`、`reference_datasheet` 和可选 `company_prior_datasheet`，但没有明确说明目标产品时，只能输出角色判断、证据包和澄清清单。即使可选我司既往产品是唯一公司产品，也不能把它自动当成目标。
- 目标型号、品牌/法务主体、交付语言或版本策略缺失时，不要创建 DOCX、不要创建交付生成脚本、不要渲染所谓生成稿。
- 不要用“先假设、再用风险标记”的方式绕过目标门禁；风险标记只适用于目标已确认后的局部参数、图形、兼容性或竞品来源事实。

无法判断模板或竞品角色时先问用户；隐藏的 Word 临时锁文件（如 `~$*.docx`）不要作为输入。

### Step 2: 建立证据包

运行角色化来源分析：

```bash
python scripts/analyze_sources.py \
  --source style_template=<style-template.docx> \
  --source reference_datasheet=<reference-datasheet.pdf> \
  --source company_prior_datasheet=<prior-company-datasheet.docx> \
  --out <analysis.json>
```

只传实际存在的角色；`style_template` 和 `reference_datasheet` 是正常必需输入，`company_prior_datasheet` 缺失时不要伪造路径。

渲染模板、竞品/参考和我司既往产品的关键页；只有目标门禁通过并已产生生成稿时，才渲染生成稿：

```bash
python scripts/render_document.py <input.docx|pdf> --out-dir <render-dir> --pages 1,2-4
```

必须在看到渲染图后再判断版式。建立证据包时至少记录：

- 首页结构：logo/title 位置、红色提示线、水印、分栏、description/features/applications 区块、页脚和页码。
- 目录规则：位置、是否在 typical application 后、字体大小、tab leader、条目和页码。
- 标题体系：styleId、大小写、字号、段前段后、分页规则。
- 表格格式：外框线、内框线、表头底色、字体字号、列宽、合并单元格、标题行规则、表后 `Notes:` 原文/用途/适用性和位置；Notes 是表格解释的一部分，不要因为正文已有风险标记就省略。
- 图片格式：来源、裁剪范围、尺寸、caption 样式、图号规则、风险说明。
- 模板批注/注释：抽取为规则，逐条处置为 `applied`、`not_applicable` 或 `needs_clarification`。
- 法务/商标样板文字：模板中的商标、版权、专利、复印限制、保密说明等 boilerplate 先归类为 `template_guidance` 或页眉页脚/notice/声明区规则；除非用户明确要求且品牌主体适用，不要混入 description、features、applications 等技术正文。
- 事实来源：用户明确事实、我司同族事实、竞品事实和缺失事实必须分开。
- 创作对象依据：为预计进入正文的标题、段落、bullet、表格行、Notes、caption、风险句、声明和图形记录来源、用途和适用边界；没有依据的对象不要进入生成稿。

不要根据当前某个样例推断所有模板都有同样章节顺序、页眉页脚结构或图表密度。用 OOXML、渲染图和来源文本交叉确认。

### Step 3: 输出 source_map.json

只有输入门禁通过后，才输出 `source_map.json` 或等价审计记录。目标门禁通过后，再创作交付 DOCX；目标门禁未通过但输入门禁已通过时，`source_map.json` 是本轮主要产物，并必须记录缺失的目标信息和澄清问题。若输入门禁未通过，不要创建 `source_map.json`、`result.md` 或占位产物，直接向用户索要输入。`source_map.json` 必须能解释正文每个关键事实、风险项、图片和版式决定从哪里来。

每条记录建议包含：

```json
{
  "id": "<stable fact id>",
  "kind": "<product_fact|format_fact|template_guidance|section_pattern|table_fact|figure_asset|risk>",
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
2. `style_template` 的批注/注释是格式和生成规则来源；必须转成 `template_guidance`。
3. `company_prior_datasheet` 用于公司术语、写法、资产和可确认的同族产品事实；跨产品复用要标边界。
4. `reference_datasheet` 用于章节框架、pin-to-pin 对照、竞品图形、待补项和风险发现；进入正文时必须标 `competitor_source` 或等效风险。

### Step 4: 设计 datasheet 草稿

只有目标门禁通过时才进入本步骤。

你负责创作设计，不要把交付质量交给固定脚本决定。先用渲染证据决定页面节奏，再写内容和实现方案。

设计每个可见元素前先过内容依据检查：

1. 这个元素解释或承载了哪个目标事实、来源事实、版式规则、风险项、用户要求或 datasheet 专业必要信息？
2. 它来自哪个 source role 和 source ref，或由哪些来源综合得出？
3. 它为什么应该出现在这个章节和这个位置；它是否符合该章节在芯片 datasheet 中的专业用途？
4. 它是否误把模板话术、竞品事实、既往产品事实或参考稿缺陷当成目标产品事实？

任何问题答不清时，不要把该元素写进正文；先补证据、改成风险项、标为不适用，或向用户澄清。

设计时至少完成：

- 首页：按模板视觉组织 description、features、applications、风险段落、logo/header/footer、水印和页码节奏。
- 章节顺序：结合竞品结构、我司既往产品和模板批注决定，不硬编码固定章节。
- 图形策略：真实图优先；可从竞品 PDF 裁图、从我司 DOCX 抽图、或创建清晰的临时示意图。所有非目标确认图都必须有风险说明。
- 表格策略：参考模板、目标事实、竞品参考和我司既往产品中有价值的表格密度和样式；缺失值写成明确风险，不交付“待补充”“从来源补充”这类空泛占位。
- Notes 策略：凡来源表格或模板要求表后 `Notes:`、`Note:`、角标解释、单位说明、stress/ESD/thermal 限制说明、包装/丝印说明，都要按当前表格/图/段落的实际内容重建或在 `source_map.json` 标为不适用；不要静默省略，也不要为了凑格式写泛泛 boilerplate。
- Notes 内容判断：先看该表/图有没有角标、缩写、单位、测试条件、来源边界、风险项或模板批注要求；Notes 只解释这些具体内容。若没有可解释对象，记录“不适用”比生成空泛 Notes 更好。
- 目录策略：目录条目和页码要与生成稿一致；如果 Word 自动域不可用，可先生成静态目录并在审计记录中说明。
- 风险策略：统一使用醒目的风险标记，例如 `TBD - NEED NCS CONFIRMATION`、`COMPETITOR BETTER - NEED REVIEW`、`SOURCE FROM COMPETITOR - NEED NCS CONFIRMATION`。
- 逐项内容策略：正文段落、features bullets、applications、表格行、图题、Notes、声明和 Important Notice 都要根据当前芯片内容和章节专业目的生成；不要复用“看起来像 datasheet”的通用句子来填版面。

最终 DOCX 正文只放 datasheet 内容。来源控制表、批注处置表、格式验证清单等内部审计内容保存在 `source_map.json`、`analysis.json`、评审记录或测试目录，不要塞进交付正文，除非用户明确要求审计稿。

模板或参考稿里的商标、logo、专利、版权和复印限制文字不属于技术正文。需要保留时，把它们放在页脚、封底 notice、首页独立声明区或 `Important Notice`，并先确认品牌主体和措辞适用于目标公司；不要把这类 boilerplate 混在首页 description 段落中。若模板在首页左栏分界线下有独立 logo/trademark 声明区，应按该区域重建，而不是删除或改写成正文句子。

### Step 5: 创作 DOCX

只有输入门禁和目标门禁都通过时才进入本步骤。目标门禁未通过但输入门禁已通过时，不要创建空白 DOCX、假设型 DOCX、交付生成脚本或生成稿渲染目录；改为把阻塞原因、已完成证据和需要用户确认的问题写入 `result.md`。输入门禁未通过时，不写 `result.md`，只向用户索要明确的输入文件路径或附件。

选择能达到目标效果的方法，而不是默认选择脚本。

可用路线：

1. **模板改造路线**：复制 `style_template` DOCX，清理占位正文，保留页眉页脚、水印、section、样式、编号、表格样式和图片关系，再用 OOXML/python-docx/Word COM 写入新内容。
2. **混合资产路线**：从 `reference_datasheet` 或 `company_prior_datasheet` 抽取/裁剪图形，按 `source_map.json` 记录来源和风险，再插入 DOCX。
3. **自定义生成路线**：为当前任务写一次性临时生成脚本，放在验证工作目录；脚本服务于当前设计，不沉淀进 skill，除非它对未来同类任务明显可复用。

生成时必须注意：

- 保留或重建模板页眉页脚和水印，不要用纯文本页眉页脚替代复杂模板。
- 替换旧型号、旧日期、旧页脚公司信息和模板占位正文。
- 清理模板商标/法务样板句；只在合适的 notice/footer/独立声明区位置保留确认适用的法务文字。
- 重建表格和图形下方的 `Notes:`/`Note:`，包括角标、缩写、测试条件、绝对最大额定说明、热性能说明和包装/丝印说明；每条 Notes 必须能指向当前表格/图形中的具体字段、角标或来源边界。
- 保留或重建两栏/单栏 section、分页、目录、表格标题行、Notes、caption 和页码。
- 插入真实图或清楚标风险的示意图；不要让“空白占位框”冒充完成内容。
- 每个竞品来源、弱于竞品项、目标事实缺失项都要在正文或风险清单中醒目标注。

### Step 6: 校验并迭代

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
  --expect "Notes:" \
  --min-tables <expected-minimum-table-count> \
  --min-drawings <expected-minimum-figure-count>
```

校验时抽查正文中的创作内容：每类可见元素至少能回指到 `source_map.json` 或分析记录中的事实、版式规则、风险项、来源边界或用户要求。发现泛泛模板句、无来源表格行、无对象可解释的 Notes、无依据 caption 或无适用主体的声明时，退回 Step 3/4 修正。

运行版式渲染：

```bash
python scripts/render_document.py <draft.docx> --out-dir <draft-render-dir> --pages 1,2-4
```

生成 side-by-side 对比图：

```bash
python scripts/compare_renders.py \
  --template-render-dir <template-render-document-dir> \
  --draft-render-dir <draft-render-document-dir> \
  --out-dir <visual-compare-dir>
```

目标门禁通过并生成 DOCX 后，如果没有生成稿渲染图，或没有把生成稿与模板、竞品/参考和我司既往产品的视觉图对照，整体结论不能是 `passed`。目标门禁未通过但输入门禁已通过时，不运行生成稿校验；结论应说明 `blocked-needs-clarification` 或等价状态。输入门禁未通过时，不写校验结论，只向用户索要明确的输入文件路径或附件。

### Step 7: 汇报产物和风险

汇报必须包含：

- 输入文档角色判断及证据。
- 若目标门禁通过并生成 DOCX，列出 DOCX、`source_map.json`、`analysis.json`、渲染图、side-by-side 对比图、资产 manifest 或临时生成脚本路径。
- 若输入门禁未通过，只列出需要用户逐项补充的输入文件路径或附件；不要伪列任何产物路径。
- 若目标门禁未通过但输入门禁已通过，列出已完成的角色判断、证据包、`source_map.json` 或等价记录、`result.md` 路径，以及阻塞的澄清问题；不要伪列 DOCX 产物。
- 已确认事实、竞品来源事实、弱于竞品项、缺失项、占位项和待用户确认项。
- 结构校验、视觉校验、CLI/平台实测的结论：`passed`、`failed` 或 `not run`；`not run` 必须说明原因。
- 仍然无法确认的产品事实和需要 NCS/产品/封装负责人确认的项目。

## When to Stop and Ask for Help

立即停止并澄清：

- 用户没有提供明确的输入文件路径或附件；此时不要扫描目录、不要枚举当前工作区或现有资产，也不要创建任何本轮产物。
- 无法判断输入文档角色，或缺少可用格式来源。
- 目标芯片型号、输出品牌/法务主体、版本策略或交付语言未提供，且无法从用户明确文字确认。
- pin-to-pin 兼容目标不明确。
- 用户只提供竞品、模板和可选我司既往产品，但没有说明要生成哪个目标产品；不要从任一输入文件擅自选择目标。
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

返回 Step 3/4：

- 发现封装或 pinout 不兼容。
- 发现参考来源、弱于参考项或图片来源不满足风险标注要求。
- 模板、产品事实、竞品参考、我司既往产品或用户意图互相冲突。

## Remember

- 按角色处理输入，不按文件名猜。
- 输入门禁先于所有脚本和产物：没有用户逐项指定的文件路径或附件时，先问用户要输入，不扫描目录、不枚举现有资产、不创建 `source_map.json`、`result.md` 或 DOCX。
- 不从竞品或我司既往产品反推目标产品；目标对象必须来自用户明确要求。
- 脚本是辅助工具，不是交付质量的上限。
- 最终 datasheet 由你基于证据自主设计；必要时写一次性临时生成脚本。
- 所有智能体创作内容都要根据当前芯片内容、来源证据和 datasheet 专业目的生成；不能为了填版面、凑格式或模仿模板而写无具体依据的文字。
- 新 datasheet 严格参照确认过的格式来源和事实来源，但不得保留模板占位正文或 Word 批注载体，也不得继承来源文档中的明显错误。
- 不把模板的商标、版权、专利、保密或复印限制样板句当作 description 正文；先判断它是页脚、notice、批注规则还是应删除的模板残留。
- 模板首页分界线下的 logo/trademark 声明区是独立声明区，不是 description 正文；需要保留时按模板位置和样式重建。
- 表格后的 `Notes:` 是 datasheet 内容的一部分；除非明确不适用，否则生成稿和校验清单都要覆盖，并且 Notes 必须根据该表格/图形的实际内容生成。
- 不把某一次用户请求、某个型号、某个文件路径、某个调试用参考结果或某句样例文字直接沉淀进 skill；先抽象成未来同类任务仍成立的角色、判断标准、禁止事项或验证步骤。
- 模板批注/注释必须转成规则并逐条处置。
- 目标产品事实优先；竞品只能提供框架、对标和带风险的临时来源。
- 缺失项、弱项、参考来源项、占位项和未确认项必须醒目标注。
- 不声明没有渲染证据支撑的版式结论。

## Integration

**Bundled scripts:**

- `scripts/render_document.py` - 渲染 DOCX/PDF，用于模板识别、生成结果视觉比对和 Word 等价验证。
- `scripts/compare_renders.py` - 生成 side-by-side 视觉对比图并输出 `visual_comparison.json`。
- `scripts/analyze_sources.py` - 解析角色化 DOCX/PDF 来源，输出结构、文本、样式、批注、表格、图片、目录线索和版式线索。
- `scripts/extract_assets.py` - 从 DOCX 来源抽取可复用图片；PDF 裁图可按任务写临时脚本。
- `scripts/verify_datasheet.py` - 检查关键文本、样式、目录线索、风险标注、表格、图片、页眉页脚和未确认项。
