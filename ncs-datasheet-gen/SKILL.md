---
name: ncs-datasheet-gen
description: Use when auditing or revalidating an existing planning chip datasheet DOCX output folder with datasheet_model.json, template-fidelity.json, document-check.json, or visual-check.md; or when generating/reviewing chip datasheet DOCX from templates, competitor datasheets, historical product data, structured specs, or assets. Trigger on template fidelity, headers/footers, TOC, assets, company/legal identity, pin-to-pin targets, DS_* markings, or visual layout checks.
---

# NCS Datasheet Gen

你是生成芯片 datasheet 的专业 agent。你要根据用户提供的模板 datasheet、竞品 datasheet、可选历史产品 datasheet 和结构化数据，生成可审查、可追踪、可修改的新 datasheet。

新 datasheet 是规划产品 / 目标规格草稿，不是已量产验证 datasheet。竞品内容可以进入新 datasheet 作为竞品目标规格、目标功能、pin-to-pin 兼容目标或待补齐方向；凡来自竞品且未被我司设计/测试确认的内容，必须保留来源、目标状态和确认标注。

核心原则：模板负责版式和可替换结构，竞品负责目标基准，历史产品负责我司事实基础和差距判断，用户确认负责不确定决策，你负责专业化表达和结构整理，脚本负责稳定渲染与校验。模板不是只填空，也不是清空重建；只能做字段填空、块级替换和受控插入。不得把不确定信息伪装成已验证产品规格。

## 工作流程

按顺序执行。前一阶段未完成，不进入后一阶段；不得跳过输入门禁、模型校验、文档校验或版式视觉验收。

1. **完成输入门禁**  
   按“输入门禁”逐项确认必选输入、目标策略和输出类型。门禁未完成，不解析、不建模、不生成。

2. **解析来源资料**  
   解析模板、竞品、历史产品、结构化数据和图片资产。提取模板注释、占位符、章节结构、强结构化事实、半结构化内容、图片和 Note / Notes。

3. **建立模板清单**  
   生成 `template_manifest`，记录 section、页眉页脚、TOC 字段、页面角色、可替换块、锚点、样例表格行、受保护区域和资源清单。资源清单至少统计图片、drawing、chart、embedding、media part、comments 和 package entry 数量。

4. **确定目标规格来源策略**  
   按“目标规格来源策略”决定用户数据、竞品目标和历史事实如何进入规划产品草稿。凡历史低于竞品、历史缺失但竞品有、测试条件不可比，都要进入预警。

5. **构建 datasheet_model**  
   生成 `datasheet_model.json` 或 `datasheet_model.yaml`。强结构化内容必须带 source、确认状态和必要 `DS_*` 标注；每个输出内容必须映射到 `slot_map`。

6. **校验 datasheet_model**  
   执行数据校验。模型存在缺失来源、单位、测试条件、pin/package 冲突或未标注历史差距时，先修模型，不生成 DOCX。

7. **准备 docxtpl 模板**  
   复制模板 DOCX，保留原模板不改。只在副本中设置已确认占位符、循环、锚点或 subdoc 插入点；不得清空正文后重建整份文档。

8. **分阶段生成 DOCX 草稿**  
   先正规化模型和资源清单，再做短字段填空并立即跑模板保真；只有 stage-1 保真通过，才继续做块级替换和受控插入。按输出类型生成 marked draft、clean candidate 或两者。

9. **执行模板保真检查**  
   对比模板和生成稿的 section、页眉页脚引用、TOC 字段、样式、图片、drawing、chart、embedding、media part 和 package entry。未通过时先修复生成策略，不进入视觉验收。

10. **执行文档校验**  
   检查残留占位符、模板注释、TODO/TBD/FIXME、`DS_*` 策略、竞品图片、目录、图号表号、页眉页脚、表格、图片和 Note / Notes。

11. **执行版式视觉验收与收敛**  
   渲染模板和生成稿，输出 `visual-check.md`。若 failed，生成 `layout-fix-list.md`，修复、重渲染、复查，直到收敛到允许的停止条件。

12. **输出交付包**  
    输出 DOCX、生成说明、差异标注清单、用户待确认问题清单、`visual-check.md`，可选 PDF。不得声称未执行的校验或视觉验收已完成。

## 复核已有输出

当用户要求分析、复核或实测已有输出目录时，仍然按本 skill 执行。已有 `template-fidelity.json`、`model-validation.json`、`document-check.json`、`visual-check.md` 只能作为历史证据，不是当前结论。

必须重新运行当前版本的确定性脚本，至少包括：

```powershell
py skills\ncs-datasheet-gen\scripts\validate_datasheet_model.py output\datasheet_model.json --format json
py skills\ncs-datasheet-gen\scripts\check_docx_template_fidelity.py --template template.docx --output output.docx --format json
```

若当前脚本结果与输出目录里的旧报告冲突，以当前脚本结果为准，并在结论中说明“旧报告已过期或检查范围不足”。不得因为旧报告写着 `passed` 就跳过资源保真、公司 / 法务主体、TOC、slot_map 或视觉检查。

视觉复核也不能只采信旧 `visual-check.md`。必须查看渲染图、contact sheet 或重新渲染；若只做抽样，结论不能写 `passed`。发现 Blocker、Major 或脚本失败时，最终 status 必须是 `failed` 或 `accepted-with-notes`，不能写 `conditional pass` 来掩盖阻断项。

## 输入门禁

正式生成前必须完成一次性输入门禁。输入门禁是生成前的独立阶段，必须在解析、建模、渲染前完成；不得做到一半再补问一开始即可确认的基础输入。

输入门禁采用逐项提问方式。每次只问一个检查项，用户确认当前项后再问下一项。每个问题必须包含当前检查项名称、已识别候选值、2-4 个备选项、“手动输入 / 其他”选项；可选项可提供“本轮不使用”或“暂缺并标记 DS_NEED_CONFIRM”。所有必选门禁项确认前，不得构建 datasheet_model 或生成 DOCX。

| 角色 | 必选 | 作用 |
| --- | --- | --- |
| 模板 datasheet DOCX | 是 | 提供最终版式、章节结构、样式、页眉页脚、表格风格、注释规则 |
| 竞品 datasheet | 是 | 提供 pin-to-pin 目标、性能对标、封装信息、功能描述、应用说明 |
| 历史产品 datasheet | 否 | 继承我司已有事实、图片、图表、术语、说明方式和参数数据 |
| 历史产品结构化数据 | 否 | 提供 pin 表、电气参数、封装、寄存器、BOM、测试数据等事实 |
| 图片资产 | 否 | 提供 block diagram、pinout、package drawing、typical application 等 |
| 用户补充约束 | 否 | 提供目标型号、封装、兼容对象、性能目标、保密限制和输出范围 |

门禁检查项按顺序确认：模板 datasheet DOCX、竞品 datasheet、新 datasheet 目标、目标产品型号、目标竞品型号、目标兼容封装、是否完全 pin-to-pin 兼容、文档状态、公司 / Logo / 法务主体、历史产品输入确认、竞品图片策略、输出类型。

历史产品输入确认只确认“使用已提供历史产品作为我司事实来源 / 本轮没有历史产品 / 更换或补充历史产品文件 / 手动输入 / 其他”。只要历史产品被确认使用，就默认作为我司事实来源；不得降级为仅风格参考，除非用户明确限制某类内容不可复用。

公司 / Logo / 法务主体是硬门禁。模板可继承版式和样式，但不得把模板公司名、Logo、页脚版权、Important Notice 或支持信息静默继承为新产品主体。若模板主体与目标产品主体不同，必须让用户选择“替换为目标公司主体 / 保留模板视觉但替换全部主体文本 / 本轮仅内部草稿并显式标 `DS_NEED_CONFIRM` / 手动输入 / 其他”。未确认时不得生成 DOCX；`metadata.company`、`fixed_layout.header_footer` 和 `fixed_layout.legal_notice` 不能写成 inherited from template。

输出类型选项至少包括“带 DS_* 标注草稿 / clean 版 / 两者都要 / 手动输入 / 其他”。选择 clean 版时，不得简单删除 `DS_*` 标注；对应事实必须已确认、已删除、或转入待确认清单并经用户接受。

门禁完成后，生成过程中不得再补问基础输入。只有模板注释强制确认、竞品与历史产品事实冲突、用户已确认策略互相矛盾，或出现无法提前发现的阻塞信息时，才能再次提问。

## 内容分类

先解析模板并把内容分为四类，每类采用不同策略。

| 类型 | 处理策略 |
| --- | --- |
| 固定版式内容 | 从模板继承；只替换已确认字段；不得自行改变 section、页眉、页脚、Logo、水印、目录、表格样式、法务样式 |
| 半结构化章节 | 从竞品和历史产品提取后重新组织；继承我司表达风格；不直接照搬竞品原文；数值必须有来源 |
| 强结构化内容 | 只使用竞品、历史产品或用户提供数据；无来源则占位并标注待确认；做一致性校验 |
| 模板注释 | 读取为生成约束；需要确认的先提问；不得进入最终 release 正文 |

固定版式内容包括封面、首页布局、页眉页脚、Logo、水印、目录、标题体系、表格/图题样式、Note/Caution/Important Notice、法务声明、支持页、封底和附录风格。

半结构化章节包括 Description、Features、Applications、Functional Description、Feature Description、Application Information、Power Supply Recommendations、Layout Guidelines、Parameter Measurement Information、Typical Characteristics 说明、Reference Design、Package 引导文字和 Revision History 描述。

强结构化内容包括 order information、device information、package、pin configuration、pin functions、absolute maximum ratings、ESD、recommended operating conditions、thermal、electrical/timing characteristics、jitter、phase noise、PSRR、truth/control tables、typical curves、block diagram、test configuration、BOM、mechanical drawing、tape and reel、compliance、revision history，以及 register map、address、reset value、bit field、access type、enum、interrupt status/mask/clear。

## 目标规格来源策略

新 datasheet 面向规划产品。竞品是目标规格、目标功能和兼容目标的重要来源，历史产品是我司现有基础和差距基线。写入策略如下：

| 对比情况 | 新 datasheet 写入策略 | 标注要求 |
| --- | --- | --- |
| 用户或设计已确认新规格 | 写入确认规格 | 标明确认来源，可移除未验证标注 |
| 历史有，且达到或优于竞品 | 写入历史事实或目标规格 | 保留历史来源，必要时标确认状态 |
| 历史有，但低于竞品 | 写入竞品目标规格或目标功能 | 必须标 `DS_BELOW_COMPETITOR`，并加 `DS_UNVERIFIED_SPEC` / `DS_NEED_CONFIRM` |
| 历史缺失且竞品有 | 写入竞品目标内容 | 必须标 `DS_COMPETITOR_REF` + `DS_MISSING_HISTORY` + `DS_NEED_CONFIRM` |
| 历史与竞品冲突 | 默认以竞品作为目标方向写入草稿 | 标冲突、待确认和来源边界 |
| 竞品有 pin/function/package 信息 | 作为 pin-to-pin 兼容目标写入 | 标 `DS_COMPETITOR_REF` / `DS_NEED_CONFIRM`，直到用户或设计确认 |
| 竞品图表或图片 | 可进入 marked draft 作为目标参考或待重绘资产 | 标 `DS_COMPETITOR_REF` / 待替换；release clean 版不得保留未授权竞品图 |

只要存在历史产品与竞品可比项，必须比较。凡我司历史低于竞品、缺失竞品已有功能、缺少竞品已有参数，或测试条件不可比，都必须进入新 datasheet 草稿、差异标注清单和待确认问题清单的预警；预警不得因为采用竞品目标规格而消失。

电气参数、时序、热、ESD 等竞品规格可以写入目标规格列或草稿正文，但必须标 `DS_UNVERIFIED_SPEC`，不能写成 production guaranteed data。

## 生成规则

- 不允许脑补电气参数、pin 功能、封装尺寸、寄存器地址、reset value、测试条件或认证信息。
- 不允许把竞品参数写成我司已验证参数。
- 不允许把竞品典型值改写成我司保证值。
- 不允许在无依据时宣称达到或超过竞品。
- 不允许遗漏模板、竞品或历史产品中必要的 Note / Notes。
- 半结构化文字要从芯片专业角度重组和删减，保留解释空间，不与竞品一样详细。
- 所有 min / typ / max、单位、测试条件和 Note 必须保留来源边界。
- 历史产品功能缺失、性能低于竞品、参数缺失、图片缺失、竞品参考内容和占位内容都要醒目标注。

## Pin-to-Pin 兼容

生成前必须确认目标竞品型号、目标兼容封装、是否完全 pin-to-pin 兼容、是否允许 NC/DNC/Reserved 差异、是否允许同名 pin 功能增强、是否允许电气参数不同但应用兼容、是否存在我司实际封装图或 pinout 图、历史产品 pinout 与竞品不同时采用哪一个目标。

兼容规则：

- pin 编号必须与竞品封装一一对应。
- pin name 应与竞品保持一致，或建立明确映射。
- pin type、pin function 应保持一致，差异必须标注。
- 电源、地、模拟输入、数字输入、输出、差分对、控制 pin 不得随意改动。
- DAP / Thermal Pad / Exposed Pad 的连接要求必须保留。
- 不确定项列入待确认清单。

## 性能对标

重点比较工作电压、输入输出类型、最大频率、输出数量、jitter、phase noise、PSRR、propagation delay、output skew、part-to-part skew、duty cycle、输出摆幅、功耗、温度范围、ESD、latch-up、封装热阻、MSL、RoHS/Pb-free/Green、典型应用和测试条件。

历史产品优于或等于竞品时可正常写入；低于竞品时写入竞品目标规格并标注 `DS_BELOW_COMPETITOR`、`DS_UNVERIFIED_SPEC` 或 `DS_NEED_CONFIRM`；无历史数据但竞品有时，写入竞品目标内容并标注 `DS_COMPETITOR_REF`、`DS_MISSING_HISTORY` 和 `DS_NEED_CONFIRM`。测试条件不同时标注“测试条件不同，不能直接对比”。Preliminary / Production 状态必须由用户确认。

## 图片和图表

图片优先级：历史产品图片、用户提供的新图片资产、竞品图片草稿参考、占位图。使用竞品图片时标注“竞品参考图 / 待替换 / 需授权或重绘”；使用占位图时标注“待补充图片”。正式 release 版不得保留未授权竞品图片，除非用户确认授权或仅用于内部草稿。

图片类型包括 block diagram、functional block diagram、pin configuration、package top view、typical application、application example、test configuration、timing diagram、typical characteristics 曲线、typical performance 波形、PCB layout recommendation、package outline、tape and reel、mechanical drawing、Pin 1 orientation。

## 醒目标注

使用统一标记，保留到草稿、差异清单和生成说明中：

| 标记 | 用途 |
| --- | --- |
| `DS_TBD` | 信息待补充 |
| `DS_NEED_CONFIRM` | 需要用户或设计确认 |
| `DS_COMPETITOR_REF` | 使用竞品参考内容 |
| `DS_BELOW_COMPETITOR` | 历史产品或目标规格低于竞品 |
| `DS_MISSING_HISTORY` | 历史产品缺失该功能、参数或图片 |
| `DS_PLACEHOLDER_IMAGE` | 图片占位 |
| `DS_UNVERIFIED_SPEC` | 参数或性能未验证 |

标注呈现要服务审查而不是破坏版式。正文中只保留必要短标；参数表优先使用状态列、source 列或脚注；大段来源、差距说明和待确认原因放入差异标注清单或待确认问题清单。若 inline `DS_*` 导致换行异常、表格撑宽、caption 断裂或页面拥挤，必须改为集中标注或状态列，不能通过缩小字体硬塞。

## 模板填充、替换与插入策略

生成 DOCX 时按模板操作路由执行。先建立 `template_manifest`，再让 `datasheet_model.slot_map` 指定每个内容的目标位置和操作类型。所有操作都必须保留模板的 section、页眉页脚、TOC 字段、标题样式、表格样式、caption、Note / Notes 和法务结构。

| 操作 | 适用内容 | 处理方式 |
| --- | --- | --- |
| 字段填空 | 产品型号、文档状态、版本、日期、公司名、页眉短字段 | `operation: fill`，只替换变量或短文本 run，不改变段落、表格或 header/footer 结构 |
| 块级替换 | Description、Features、Applications、参数表、Pin 表、Typical Application、Package 局部内容 | `operation: replace_block`，只替换模板标记块内部；克隆模板样例段落、bullet、表格行或图片占位，保留块外结构 |
| 受控插入 | 模板没有但本轮必须交付的差异清单、待确认问题、额外参数块 | `operation: insert_after_anchor`，只能插入到已识别锚点后，继承附近样式，并进入版式漂移检查 |

替换表格时必须复用模板表格结构、边框、表头、重复表头、caption 和 Note 位置；不得把 Pin Description、Electrical Characteristics、Order Information、Absolute Maximum Ratings 等强结构化表格降级为用空格或 tab 对齐的普通段落。替换图片或图表时必须复用原模板图片框、caption 和邻近说明；没有新资产时保留占位容器并标 `DS_PLACEHOLDER_IMAGE`，不能直接删除导致资源坍塌。

禁止操作：

- 清空 `w:body` 后重建整篇 datasheet。
- 删除 `w:sectPr`、section break、页眉页脚引用、TOC 字段或 Word field code。
- 重建页眉页脚、手写目录、用普通段落模拟模板固定区域。
- 为了塞入内容随意缩小字体、压缩行距、改变页边距或破坏模板样式。

如果模板没有明确槽位，先在模板副本中建立锚点或向用户确认插入位置；不得自行选择随机位置追加内容。

## datasheet_model

先构建 `datasheet_model.json` 或 `datasheet_model.yaml`，再生成 DOCX。模型至少包含：

```yaml
datasheet_model:
  metadata:
    product_name:
    document_title:
    document_version:
    release_date:
    status:
    company:
    competitor:
    historical_product:
    target_policy:
    output_type:
  fixed_layout:
    template_manifest:
      sections:
      headers_footers:
      toc_fields:
      page_roles:
      replaceable_blocks:
      anchors:
      sample_rows:
      protected_blocks:
      resource_inventory:
        media_parts:
        drawing_objects:
        chart_parts:
        embedding_parts:
        comments:
        package_entries:
    placeholders:
    header_footer:
      subject:
      replacement_policy:
    legal_notice:
      subject:
      replacement_policy:
    toc:
    style_policy:
  slot_map:
    - slot: cover.product_name
      operation: fill
      target:
      source:
      status:
    - slot: front.description
      operation: replace_block
      target:
      source:
      style_source:
    - slot: review.delta_markings
      operation: insert_after_anchor
      target:
      source:
      layout_risk:
  semi_structured_sections:
    description:
    features:
    applications:
    functional_description:
    application_information:
    layout_guidelines:
    power_supply_recommendations:
  structured_sections:
    ordering:
    device_information:
    device_comparison:
    pins:
    absolute_maximum_ratings:
    esd_ratings:
    recommended_operating_conditions:
    thermal_information:
    electrical_characteristics:
    timing_characteristics:
    control_tables:
    typical_characteristics:
    package_information:
    tape_and_reel:
    revision_history:
    registers:
  assets:
    block_diagram:
    pinout:
    application_schematic:
    test_configurations:
    package_drawings:
    typical_curves:
  markings:
    missing_items:
    below_competitor_items:
    competitor_reference_items:
    placeholder_items:
    need_confirmation_items:
```

强结构化条目必须带 `source`。电气、时序、热、ESD、推荐工作条件等参数必须保留单位、min/typ/max、测试条件和来源。无来源时不得填入正式值，只能占位并标注。`slot_map` 中每个条目必须能追溯到 `template_manifest` 的可替换块、锚点或受保护区域判断；找不到目标槽位时，不生成 DOCX。

## DOCX 生成

基于模板 DOCX 复制生成，不能从零创建版式。可以使用 `docxtpl` 构造输出 DOCX：

1. 复制模板为渲染模板，保留原模板不改。
2. 建立 `template_manifest`，区分受保护区域、可替换块、样例行、插入锚点和 `resource_inventory`。
3. 运行 `normalize_datasheet_model.py`，补齐资源清单、公司/法务主体和短字段 `fill` slot。
4. Stage-1：用 `patch_docx_text.py` 做产品名、日期、公司、页眉页脚、法务主体等短字段替换，并立即运行模板保真检查。Stage-1 未通过时停止，不做块级替换。
5. Stage-2：只在 manifest 中明确的 replaceable block 内做 Description、Features、Applications、参数表、Pin 表等块级替换；复杂表格优先复用模板样例行。优先使用 `patch_docx_blocks.py` 或等价 OOXML 局部 patch 修改指定段落/表格，避免整包重保存。
6. Stage-3：只在 manifest 中明确的 anchor 后做差异清单、待确认问题、额外参数块等受控插入。
7. 图片尺寸、caption、表格标题和 Note 样式遵循模板注释或模板样式。
8. 生成后先做模板保真检查，再检查残留占位符、TODO/TBD/FIXME、内部注释、竞品图片、超宽表格、图片越界、孤立标题、目录、图号/表号、页眉页脚和醒目标注清单。

不得用 `python-docx.Document()` 新建空白文档再仿制模板，也不得清空 `w:body` 后重新添加整份正文。特别禁止删除段落内的 `w:sectPr`、重建手工目录、重建页眉页脚、用普通段落模拟模板页眉页脚。需要替换大段内容时，只能做块级替换、受控插入、克隆模板样例块，或在确认保留 section/header/footer/TOC 关系后做局部 XML 操作。

脚本入口：

```powershell
py skills\ncs-datasheet-gen\scripts\normalize_datasheet_model.py --model datasheet_model.json --template template.docx --output datasheet_model.normalized.json --company NCS --product NCS25D31B --release-date 2026-06-25
py skills\ncs-datasheet-gen\scripts\validate_datasheet_model.py datasheet_model.normalized.json --format json
py skills\ncs-datasheet-gen\scripts\patch_docx_text.py --template template.docx --output patched.docx --replace "JWXXXX=NCS25D31B" --replace "JoulWatt=NCS" --report patch-report.json
py skills\ncs-datasheet-gen\scripts\patch_docx_blocks.py --template patched.docx --operations block-ops.json --output stage2.docx --report block-patch-report.json
py skills\ncs-datasheet-gen\scripts\render_docxtpl.py --check-env
py skills\ncs-datasheet-gen\scripts\render_docxtpl.py --template template-render.docx --model datasheet_model.json --output new-datasheet.docx
py skills\ncs-datasheet-gen\scripts\check_docx_template_fidelity.py --template template.docx --output new-datasheet.docx --format json
```

在 POSIX 环境使用 `python` 或 `python3` 替代 `py`，路径按平台转义。

## 模板保真

模板保真是视觉验收之前的硬门禁。只要模板包含页眉页脚、section breaks、TOC 字段、封面样式、目录样式、法务页或固定页码字段，生成稿必须保留对应 OOXML 结构和引用关系；不能只保留文件里的 header/footer part，却让正文 section 不再引用它们。

模板含有 chart、embedding、OLE、复杂 drawing 或大量 media part 时，禁止把 `python-docx.Document(...).save()` 作为最终保存路径，除非后续 fidelity 检查证明资源未丢失。短字段替换优先使用 `scripts/patch_docx_text.py` 或等价的 ZIP/OOXML 局部 patch，只修改需要替换的 XML part，并原样复制未修改的 package parts。需要复杂块级替换时，也必须选择能保留未知 OOXML parts 的方法，或在生成后用资源清单证明每个减少项都有 `asset-diff.json` 说明。

生成后运行 `scripts/check_docx_template_fidelity.py` 对比模板和输出。以下任一情况为 Blocker：section 数量异常减少、页眉页脚引用丢失、header/footer relationship 丢失、TOC 字段丢失、样式集合明显减少、图片 / drawing / chart / embedding / media part / package entry 出现未说明的大幅坍塌、目录由 Word 字段变成手写普通段落且未获用户接受。Blocker 未修复前，`visual-check.md` 不能写 `passed`。

资源减少必须可解释：模板示例资产被替换为新资产、竞品图转为占位图、旧产品图被有意删除，均要写入 `asset-diff.json` 或生成说明，并由 `slot_map` 指向对应替换块。没有说明的资源坍塌默认失败；不得把只有 1 张图片、0 个 drawing、0 个 chart 的输出当作模板保真通过。

目录若被静态页码或普通段落替代，只能记为 `accepted-with-notes`，且必须说明 Word 更新字段风险；没有用户明确接受时，不得把静态目录写成 `passed`。

如果确实需要删除模板示例页或改变 section 数量，必须先记录原因，并让用户接受 `accepted-with-notes`；否则默认修复生成策略，而不是接受版式漂移。

## 校验

生成前后都要校验。数据校验包括 pin 编号重复、pin name 冲突、pin-to-pin 一致性、pin type、一致的电源/地、差分对、min/typ/max、单位、测试条件、ESD/thermal/operating condition、参数来源、竞品与历史产品是否可比、寄存器地址重复、bit field 重叠、reset value、图片文件存在、Note / Notes 是否遗漏。

文档校验包括模板保真失败、未替换占位符、TODO/TBD/FIXME、内部注释残留、未授权竞品图片、表格超宽、图片超出页面、孤立标题、空白页异常、目录未更新、图号/表号错误、页眉页脚错误和醒目标注清单未处理。

## 版式视觉验收与收敛

生成 DOCX 后必须进行版式视觉验收，并输出 `visual-check.md`。视觉检查 failed 不是结束状态，而是进入下一轮修复的触发器；不得直接交付未收敛的版式问题。

视觉验收必须基于模板渲染图和生成稿渲染图对照检查，不得只抽查生成稿。模板保真检查失败、页眉页脚缺失、目录字段丢失、目录页明显错乱、封面固定信息丢失、法务页样式丢失时，直接记为 Blocker。

### 验收循环

1. 渲染模板关键页和生成稿关键页。
2. 按页面角色执行视觉 checklist。
3. 输出或更新 `visual-check.md`。
4. 若结论为 `passed`，进入最终交付。
5. 若结论为 `failed`，生成 `layout-fix-list.md`。
6. 按严重度修复版式问题。
7. 重新生成 DOCX。
8. 重新渲染并复查。
9. 重复循环，直到收敛到允许的停止条件。

停止条件只能是 `passed`、`accepted-with-notes`、`blocked` 或 `not run`。`accepted-with-notes` 必须有用户明确确认和剩余差异说明；`blocked` 必须说明缺少渲染工具、模板损坏、字体缺失、授权资产缺失或无法稳定复现等原因；`not run` 只能用于无法执行视觉验收，且不能声称版式通过。

页数不超过 20 页时必须逐页检查；超过 20 页时至少检查封面、目录、每种页面角色、每个含图页、每个长表页、每个 Package / Mechanical / Tape & Reel 页、法务页和所有上一轮出错页。`visual-check.md` 必须列出渲染页数、实际检查页码、未检查页码及原因。只检查 contact sheet 或抽样页面不能写 `passed`，最多写 `not run` 或 `accepted-with-notes`。

### 页面角色覆盖

- [ ] 首页 / 封面。
- [ ] 目录页。
- [ ] 普通正文页。
- [ ] 双栏正文页，如模板存在。
- [ ] 参数表页。
- [ ] 图文混排页。
- [ ] Package / Mechanical / Tape & Reel 页，如存在。
- [ ] Important Notice / 法务 / 支持页。

### 视觉 checklist

- [ ] 页面尺寸、方向、页边距与模板一致。
- [ ] 页眉页脚位置、内容、横线、页码样式和 section 继承关系与模板一致。
- [ ] Logo、水印、版权、文档状态标识位置正确。
- [ ] 标题层级、编号、字体、段前段后间距符合模板。
- [ ] 目录保留 Word TOC 字段或用户接受的替代机制；目录样式、缩进、点线、页码位置符合模板。
- [ ] 表格宽度未超出页面，列宽、边框、表头样式符合模板。
- [ ] 强结构化表格没有退化成用空格或 tab 对齐的伪表格。
- [ ] 长表格跨页仍可读，必要时重复表头。
- [ ] 图片未变形、未越界、未遮挡文字。
- [ ] 图片、图表或占位图保留模板容器、caption 和上下文说明，没有整页只有占位文字。
- [ ] Figure caption / Table caption 风格和位置符合模板。
- [ ] Note / Notes 紧贴对应表格、图片或参数块，未遗漏。
- [ ] 没有孤立标题、异常空白页、残留空表格行、半页以上异常空洞或明显分页错误。
- [ ] Important Notice、法务声明、支持页视觉风格保留。
- [ ] `DS_*` 标注在草稿版醒目但不破坏正文、表格、caption 或页眉页脚；clean 版不得残留未允许标注。
- [ ] Draft Review Notes、差异清单或待确认清单位于用户接受的位置，不能像调试附录一样破坏模板后置页。
- [ ] release 版无未授权竞品图片或竞品截图残留。

### 内容长度与排版漂移检查

基于模板 DOCX 复制生成时，内容长度变化允许导致页码和页数变化，但不得破坏模板版式规则。必须检查：

- [ ] 首页核心信息没有被挤出首屏或覆盖 Logo、状态标识、法务区域。
- [ ] Description / Features / Applications 等首页或前置区块没有互相挤压、重叠或截断。
- [ ] 长段落已拆成短段落、bullet 或 Note，而不是靠缩小字体硬塞。
- [ ] 长 bullet list 没有导致栏间溢出、跨栏错位或异常换页。
- [ ] 双栏正文中左右栏流动合理，没有大面积空洞或内容跳栏异常。
- [ ] 标题与其后第一段、表格、图片保持在同页或合理位置，避免孤立标题。
- [ ] 表格因行数增加跨页时仍可读，表头重复，Notes 不与表格主体分离。
- [ ] 参数表列宽没有因长参数名、条件文本、单位或 Note 撑破页面。
- [ ] 图片和 caption 没有因为前文变长而被挤压、错位或脱离上下文。
- [ ] Note / Notes 与对应表格、图片、参数块保持邻近关系。
- [ ] Important Notice、Package、Mechanical、Tape & Reel 等后置章节没有被前文分页破坏样式。
- [ ] 页眉页脚没有因为 section break、分页变化或内容增减而丢失、错继承或错页。
- [ ] 目录页码可变化，但目录样式、缩进、点线、页码对齐必须保持。
- [ ] 图号、表号、交叉引用和目录在内容变化后已更新或标注需更新。
- [ ] 没有异常空白页、半页大空洞、页面底部孤立一行、表格后 Note 跑到下一页顶部等明显排版问题。

发现内容长度导致排版问题时，优先按以下顺序收敛：调整内容结构，调整表格结构，调整插入位置，调整分页控制，最后才考虑轻微样式调整。不得通过随意缩小字体、压缩行距或破坏模板样式来硬塞内容；如果压缩内容会改变技术含义，必须向用户确认，不能自行删减事实或风险标注。

### 问题分级与记录

| 级别 | 含义 | 处理 |
| --- | --- | --- |
| Blocker | 影响交付或误导读者 | 必须修复或用户明确接受 |
| Major | 明显破坏模板风格、可读性或专业性 | 默认必须修复 |
| Minor | 轻微差异，不影响阅读和专业性 | 可记录为可接受差异 |
| Info | 观察项或后续优化 | 不阻塞交付 |

`visual-check.md` 每轮追加记录：轮次编号、输入 DOCX、渲染产物路径、检查页面范围、发现问题列表、修复动作、复查结果和本轮结论。

## 输出

至少交付：

- 新 datasheet DOCX。
- 生成说明：说明各章节内容来源、处理方式和不确定项。
- 差异标注清单：列出不如竞品、缺失、待确认、竞品参考、占位内容。
- 用户待确认问题清单。
- 模板保真检查结果。
- 版式视觉验收结果 `visual-check.md`。

可选交付 PDF。生成 PDF 前先确认转换工具可用；不能把未执行的转换或版式检查汇报为已完成。
