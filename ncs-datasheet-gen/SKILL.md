---
name: ncs-datasheet-gen
description: Use when creating, revising, formatting, validating, or maintaining an NCS/company semiconductor datasheet from DOCX/PDF source documents, especially when the template, reference, prior company document, or product facts may have different structures or styles.
---

# NCS Datasheet Gen

## Overview

你要把不同结构的 DOCX/PDF 输入文档归一化成可追溯原材料，再由你编排 `content.json`，最后用确定性 DOCX renderer 生成并验证 datasheet。脚本负责渲染、清模板正文、输出中移除批注载体和结构校验；你负责判断文档角色、抽取事实、组织章节、处置模板批注规则和标记风险。

**开始时说明：**“我会使用 ncs-datasheet-gen 流程，先按角色梳理输入文档，再生成可追溯的 `content.json` 和 DOCX 草稿。”

## Script Environment

使用 Python 3.10+ 运行 `scripts/` 中的工具。开始处理文档前执行：

```bash
python scripts/render_document.py --probe
python scripts/render_document.py --install-help
```

首次使用任一脚本前运行该脚本的 `--help`，确认命令入口可用。

- `analyze_sources.py`、`extract_assets.py`、`verify_datasheet.py` 的 DOCX 基础解析使用 Python 标准库。
- `scripts/requirements.txt` 提供 `PyMuPDF`、`python-docx` 和 Windows Word COM 所需的 `pywin32`。
- `render_document.py` 渲染 DOCX 还需要 Microsoft Word COM 或 LibreOffice 的 `soffice`。
- 如果 Word/LibreOffice 不可用，`render_document.py --engine docx-preview` 可生成结构化版式预览图；它不是 Word 等价渲染，只能用于模板视觉结构、页数、栏数、图表密度和粗粒度差距诊断。
- 依赖、Word COM 或 LibreOffice 缺失且无法安装时，记录缺失项、命令和错误输出；只汇报已完成的验证项。

## The Process

### Step 1: 按角色澄清输入

按角色而不是文件名理解输入文档。同一文件可以承担多个角色，某个角色也可以缺失，但缺失会改变风险标注和输出边界。

| 角色 | 常见格式 | 用途 | 约束 |
| --- | --- | --- | --- |
| `style_template` | DOCX 优先，PDF 只能作视觉参考 | 样式、页眉页脚、section、栏数、目录、表格、图片版式、模板批注/注释规则 | 只复用格式，不保留占位正文；批注内容要先转成规则再从输出移除 |
| `reference_datasheet` | PDF/DOCX | 竞品或公开参考的章节框架、对标项、待补充项 | 不把参考参数写成我司承诺 |
| `company_prior_datasheet` | DOCX/PDF | 我司既有术语、写法、可复用确认事实、可复用图片 | 不替代目标产品事实 |
| `target_product_facts` | DOCX/PDF 或用户提供事实包 | 目标产品型号、封装、pin、规格、限制、版本信息 | 最高优先级；缺失时必须标风险 |

确认目标芯片型号、功能定位、封装、版本号、日期、输出路径、语言、pin-to-pin 兼容对象、风险标注格式和是否允许先出带风险的草稿。

如果只有 PDF 作为 `style_template`，说明无法直接继承 Word 样式、页眉页脚和 section；只能用它做视觉参考，或要求用户提供 DOCX 模板。

### Step 2: 分析输入文档

运行角色化来源分析：

```bash
python scripts/analyze_sources.py \
  --source style_template=<style-template-or-visual-reference.docx> \
  --source reference_datasheet=<reference-datasheet.pdf> \
  --source company_prior_datasheet=<prior-company-datasheet.docx> \
  --source target_product_facts=<target-product-facts.docx> \
  --out <analysis.json>
```

只传实际存在的角色；缺失角色不要伪造路径。运行模板或参考文档渲染：

```bash
python scripts/render_document.py <input.docx|pdf> --out-dir <render-dir> --pages 1,2-4
```

必须产出 `style_template`、关键参考文档和生成稿的渲染图后再判断版式。DOCX 真实渲染失败时，不得声称已参考模板排版；把该验证项记录为 `failed` 或 `not run`，并说明 LibreOffice/Word COM 错误。为了继续做粗粒度视觉诊断，可以显式运行：

```bash
python scripts/render_document.py <input.docx> --engine docx-preview --out-dir <preview-render-dir> --pages 1,2-4
```

`docx-preview` 结果必须在报告中标注“不是 Word 等价渲染”。它只能支持 gross layout comparison，不能替代最终 Word/LibreOffice 渲染通过。

建立格式事实清单，至少覆盖：

- 首页结构：分栏、section break、column break、页眉、页脚、水印、logo 区域、首页页码
- 标题体系：各级 styleId、显示大小写、字号、字体、段前段后、分页规则
- 列表体系：一级和二级 numId、缩进、制表位、符号；不允许用默认项目符号代替已识别的模板编号体系
- 目录规则：CONTENTS 位置、TOC 样式、tab leader、页码格式、哪些章节进入或不进入目录
- Notes/Note：表格后注释段的位置、原文、用途、适用性、替代处理
- 表格格式：外框线、内框线、表头底色、字体字号、列宽、合并单元格、标题行规则
- 图片格式：位置、尺寸、caption 样式、图号规则、来源标注、占位图写法
- 模板批注/注释：先抽取为 `comment_guidance`，再转入 `source_map.json` 的 `template_guidance`；逐条处置为 `applied`、`not_applicable` 或 `needs_clarification`，写明证据；不得直接丢弃，也不允许把 Word 批注载体保留到新文档
- 模板视觉布局：从模板渲染图或 `docx-preview` 图提取首页区域、两栏/单栏、目录位置、图表节奏、表格连续性、页眉页脚占位、正文密度和每页主要模块，写入 `source_map.json` 的 `format_fact` 或 `section_pattern`

对不确定格式使用 OOXML、PDF 渲染图、截图或解析脚本确认。不要根据当前某个样例推断所有模板都有同样的章节顺序、样式名、表格列或页眉页脚结构。

### Step 3: 生成 source_map.json

先输出 `source_map.json`，再写 `content.json`。`source_map.json` 是你对原材料的归一化结果，不要求 renderer 直接消费，但必须可审计。

每条事实建议包含：

```json
{
  "id": "<stable fact id>",
  "kind": "<product_fact|format_fact|template_guidance|section_pattern|table_fact|figure_asset|risk>",
  "normalized_fact": "<normalized claim, layout rule, or missing item>",
  "source_role": "<style_template|reference_datasheet|company_prior_datasheet|target_product_facts|user>",
  "source_ref": "<file name + page/section/table/paragraph reference>",
  "confidence": "<confirmed|needs_confirmation|reference_only|conflict>",
  "risk": "<missing|weaker|competitor_source|none>",
  "notes": "<brief handling instruction>"
}
```

事实优先级：

1. 用户明确事实和 `target_product_facts` 用于目标产品承诺。
2. `style_template` 的批注/注释是格式和生成规则来源；先转成 `template_guidance` 并逐条处置，不能因为最终 DOCX 不保留批注就忽略其内容。
3. `company_prior_datasheet` 用于公司术语、写法、资产和可确认的同族产品事实；跨产品复用时要标注适用边界。
4. `reference_datasheet` 用于章节框架、对标项、风险发现和临时占位；引用到正文时必须标 `competitor_source` 或等效风险。
5. 任何来源冲突、目标事实缺失、弱于参考、图片来源不明或 pin/package 不确定，都进入风险表。

### Step 4: 编排 content.json

你根据 `source_map.json` 编排 `content.json`。章节不固定，按目标产品、参考结构和模板目录规则决定；不要把 `DESCRIPTION`、pin 表或 revision history 当成所有文档必有的硬编码结构。

编排时要按模板视觉事实先做版式规划，再写正文：

1. 用模板渲染图确定首页模块和栏目分布，例如 description/features/applications、contents、typical application、order/device information 等区域。
2. 用参考/既往产品文档确定目标产品应覆盖的章节、表格和图；不能因为 renderer 能输出段落就省略 block diagram、pin diagram、electrical characteristics、package 等常见 datasheet 模块。
3. 把 `content.json.sections` 排成接近模板视觉节奏的顺序：短说明和 features 先行，pin/ratings/electrical tables 成组，图形用真实资产或带风险的 `image_placeholder` 占位。
4. 不把来源控制、模板指导处置、格式验证说明放进交付正文；这些内容保存在 `source_map.json` 或单独审计稿。

最小结构：

```json
{
  "product": {
    "name": "<target_part_number>",
    "subtitle": "<datasheet subtitle>",
    "revision": "<revision or TBD>",
    "date": "<YYYY/MM/DD or TBD>",
    "compatibility": "<pin-to-pin compatibility statement or TBD>"
  },
  "sources": {
    "input_documents": [
      {"role": "style_template", "path": "<path>", "purpose": "format/style/layout only"},
      {"role": "reference_datasheet", "path": "<path>", "purpose": "framework and comparison"},
      {"role": "company_prior_datasheet", "path": "<path>", "purpose": "company wording and reusable assets"},
      {"role": "target_product_facts", "path": "<path>", "purpose": "authoritative target facts"}
    ],
    "analysis_report": "<analysis.json>",
    "source_map": "<source_map.json>",
    "asset_manifest": "<assets.json>"
  },
  "template_guidance": [
    {
      "source_role": "style_template",
      "source_ref": "<template comment id or source_map id>",
      "instruction": "<template comment or annotation guidance>",
      "decision": "<applied|not_applicable|needs_clarification>",
      "evidence": "<where this guidance was applied, or why it does not apply>"
    }
  ],
  "risk_markers": {
    "missing": "TBD - NEED NCS CONFIRMATION",
    "weaker": "COMPETITOR BETTER - NEED REVIEW",
    "competitor_source": "SOURCE FROM COMPETITOR - NEED NCS CONFIRMATION"
  },
  "sections": [
    {
      "title": "<section title selected from source_map>",
      "blocks": [
        {
          "type": "paragraph",
          "text": "<agent-authored text from confirmed facts>",
          "source_ref": "<source_map fact id>",
          "confidence": "confirmed"
        },
        {
          "type": "paragraph",
          "risk": "competitor_source",
          "text": "<reference-derived text pending confirmation>",
          "source_ref": "<source_map fact id>",
          "confidence": "needs_confirmation"
        }
      ]
    }
  ],
  "risk_items": [
    {"kind": "missing", "text": "<unresolved item tied to source_map>"}
  ]
}
```

支持的 block 类型：

- `paragraph`：正文段落；带 `risk` 时渲染红色风险前缀。
- `bullets`：项目符号列表；`items` 可以是字符串，也可以是 `{"text": "...", "risk": "...", "source_ref": "..."}`。
- `table`：表格；单元格等于任一 risk marker 时自动红色粗体。
- `note`：加粗 note 段落；带 `risk` 时渲染红色风险前缀。
- `warning`：显式风险段落，使用 `kind` 或 `risk`。
- `image_placeholder`：图片占位，必须带风险标记，直到真实图片可用。

不要把“待映射”“写在这里”“从来源补充”这类占位句交给用户当完成内容。确实缺事实时，用风险 marker 和待确认清单表达。

`template_guidance` 里的每条模板批注/注释都必须有处置结果。`applied` 要说明应用到哪个章节、表格、样式或版式事实；`not_applicable` 要说明不适用原因；`needs_clarification` 要进入待确认清单。

### Step 5: 生成 DOCX

初始化配置：

```bash
python scripts/generate_datasheet.py --init-config <content.json>
```

生成 DOCX：

```bash
python scripts/generate_datasheet.py --config <content.json> --output <draft.docx>
```

生成器只渲染 `content.json`。当 `sources.input_documents` 中存在可读取的 DOCX `style_template` 时，生成器会复用其样式、编号定义、section properties、页眉页脚和表格基础样式，并清除模板占位正文。模板批注/注释必须先进入 `template_guidance` 并逐条处置；生成器只在输出中移除批注载体，不删除已经转写成规则的内容。PDF 模板只作为人工视觉参考，不会被 renderer 当作 DOCX 样式源。

最终交付 DOCX 正文只放 datasheet 内容。来源控制表、模板批注处置表、格式验证清单等内部审计内容保存在 `source_map.json`、评审记录或单独审计稿中；只有需要非交付审计稿时，才显式设置 `output_options.include_audit_sections: true`。

### Step 6: 校验并汇报

运行结构校验：

```bash
python scripts/verify_datasheet.py --docx <draft.docx> --expect "<required text>" --risk-marker "<red marker>" --forbid-comments --forbid-body-text "<template placeholder text>"
```

如模板事实要求两栏或页眉页脚，增加：

```bash
python scripts/verify_datasheet.py --docx <draft.docx> --require-body-two-column --min-body-section-header-footer-refs 1
```

交付稿还必须禁止模板残留、内部审计章节和错误页眉页脚：

```bash
python scripts/verify_datasheet.py --docx <draft.docx> \
  --forbid-body-text "SOURCE AND RISK CONTROL" \
  --forbid-body-text "TEMPLATE GUIDANCE DISPOSITION" \
  --forbid-body-text "FORMAT VERIFICATION REQUIREMENTS" \
  --forbid-header-footer-text "<template-placeholder-or-old-part-number>" \
  --forbid-header-footer-text "<old-company-or-template-brand>" \
  --min-tables <expected-minimum-table-count> \
  --min-drawings <expected-minimum-figure-count>
```

运行版式渲染：

```bash
python scripts/render_document.py <draft.docx> --out-dir <draft-render-dir> --pages 1,2-4
```

把模板渲染图、我司既往产品渲染图、竞品/参考渲染图和生成稿渲染图放在同一验证目录中对照。若使用 `docx-preview`，模板和生成稿必须使用同一个 engine 与 dpi。生成 side-by-side 对比图：

```bash
python scripts/compare_renders.py \
  --template-render-dir <template-render-document-dir> \
  --draft-render-dir <draft-render-document-dir> \
  --out-dir <visual-compare-dir>
```

检查目标型号、版本、日期、pin 名、兼容声明、关键章节、风险标记、来源标注、占位标注、标题 styleId、TOC 样式、列表 numId、Notes/Note、body 级 section、页眉页脚引用、表格数量、图片数量、首页密度、分栏、图表位置、标题层级、模板批注/注释已转成 `template_guidance` 并逐条处置、模板批注载体不得残留、模板占位正文不得残留、页眉页脚替换。查看 `compare_renders.py` 生成的 side-by-side 图和 `visual_comparison.json`，把明显差距反馈回 Step 3/4：页数过少、首页模块错位、图表密度不足、目录缺失、连续表格断裂、内部审计内容入正文、页眉页脚仍是模板占位，都必须修正或标为 failed。

如果没有生成稿渲染图，或没有把生成稿与模板视觉图对照，整体结论不能是 `passed`。汇报生成产物、`content.json`、`source_map.json`、分析报告、渲染图、资产 manifest、校验报告、输入文档角色、模板格式事实清单、缺失项、弱项、参考来源项、占位项、待确认项，以及 passed、failed、not run 的验证项和原因。

## When to Stop and Ask for Help

**立即停止并澄清：**

- 无法判断输入文档角色，或缺少可用的格式来源
- pin-to-pin 兼容目标不明确
- 模板批注、Notes/Note 或版式事实无法判断
- 模板批注/注释无法判断是否适用，且无法写出明确处置证据
- 来源数据互相冲突，且无法确定优先级
- 目标事实缺失，但用户不允许风险标注或占位
- 用户未确认风险标注格式
- 渲染或校验失败，且无法判断生成文档是否符合模板

**不要猜测未确认的产品参数、封装兼容性、缺失功能或来源归属。**

## When to Revisit Earlier Steps

**返回 Step 1：**

- 用户更换任一输入文档角色
- 用户调整目标芯片、封装、兼容对象、输出语言或标注策略

**返回 Step 2：**

- 模板版本变化
- 渲染图和 OOXML 解析结果不一致
- 目录、列表、批注、表格或图片规则仍不确定

**返回 Step 3：**

- 发现封装或 pinout 不兼容
- 发现参考来源、弱于参考项或图片来源不满足风险标注要求

## Remember

- 按角色而不是文件名处理输入。
- 先做 `source_map.json`，再写 `content.json`。
- 新 datasheet 的格式和排版严格参照确认过的格式来源，但不得保留模板占位正文或 Word 批注载体。
- 按模板视觉渲染结果排版：先看模板视觉，再编排 `content.json`，生成后用 side-by-side 对比回看，不要只靠 XML 结构检查。
- 模板标注/注释是生成规则来源；必须先转成 `template_guidance` 并逐条处置，不得直接丢弃。
- 脚本不是内容作者；你必须完成事实判断、章节编排和风险标注。
- 目标产品事实优先；参考文档只能提供框架、对标和带风险的临时来源。
- 缺失项、弱项、参考来源项、占位项、未确认项必须醒目标注。
- 不声明没有渲染证据支撑的版式结论。

## Integration

**Bundled scripts:**

- `scripts/render_document.py` - 渲染 DOCX/PDF，用于模板识别和生成结果视觉比对
- `scripts/compare_renders.py` - 对模板和生成稿的 PNG 渲染结果做 side-by-side 视觉对比并输出 `visual_comparison.json`
- `scripts/analyze_sources.py` - 解析角色化 DOCX/PDF 来源，输出结构、文本、样式、批注、表格、图片、目录线索和版式线索
- `scripts/extract_assets.py` - 从我司既有产品文档抽取可复用图片，并按配置排除不兼容资产
- `scripts/generate_datasheet.py` - 生成配置模板并按配置生成目标 DOCX
- `scripts/verify_datasheet.py` - 检查关键文本、样式、目录线索、编号、风险标注、表格、图片、页眉页脚和未确认项
