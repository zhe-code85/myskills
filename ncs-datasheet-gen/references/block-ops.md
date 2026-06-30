# Block Operations Rules

当你生成、修改或审查 `block-ops.json`、`patch_docx_blocks.py`、模板锚点、表格替换或受控插入时，读取并执行本文件。

## 基本原则

- 先建立 `template_manifest`，再生成 block ops。
- 每个操作都必须来自 `datasheet_model.slot_map`、`template_manifest` 锚点、或脚本可解释的模板槽位。
- 不要手写临时 JSON 作为交付链路；应运行 `build_block_ops_from_model.py` 生成。
- `patch_docx_blocks.py` 应使用 `--require-source-slots`，确保每个 paragraph / table / insert 操作带 `source_slot`。
- 不得清空 `w:body` 后重建整篇 datasheet。
- 不得删除 `w:sectPr`、section break、页眉页脚引用、TOC 字段或 Word field code。

## 操作类型

| JSON 字段 | 用途 | 约束 |
| --- | --- | --- |
| `paragraphs[].index/text` | 替换或清空指定正文段落 | 默认保留段落内 drawing / pict，避免误删模板视觉对象 |
| `paragraphs[].preserve_visuals` | 控制清段落时是否保留视觉对象 | 只有旧模板示例图、错误 pinout 或已被新资产替代时才能设为 `false` |
| `clear_paragraph_ranges[].start/end` | 清空一段连续段落 | 用于清理旧章节正文；必须带 `source_slot`，默认保留视觉对象，只有旧示例图或错误图才设 `preserve_visuals: false` |
| `replace_paragraph_ranges[].start/end/paragraphs` | 用多段新内容替换一个段落范围 | 用于章节级替换；范围内剩余段落必须被清空，不得留下旧正文 |
| `remove_visuals_in_ranges[].start/end` | 删除范围内旧 drawing / pict / object | 只用于旧 logo、旧 pinout、旧应用图、旧 package 图或已由占位图替代的视觉对象 |
| `tables[].index/rows` | 替换指定模板表格 | 用于 Pin Description、Device Information、Electrical Characteristics 等强结构化表格 |
| `remove_tables` | 删除指定模板示例表 | 只删除已确认不属于目标产品的旧示例表，并在报告中记录 |
| `insert_tables_after_paragraphs` | 在指定段落后插入占位表或新增结构化块 | 只能插入到已识别锚点后，插入后必须做视觉漂移检查 |
| `remove_empty_trailing_paragraphs` | 删除正文末尾空段落 | 用于防止尾部空白页；不得删除带 section 属性的段落 |

每个对象应带 `source_slot`，例如 `pins.pin_configuration`、`tables.thermal_information`、`front.description`。

如果生成过程中需要 `augment_block_ops.py`、`final_cleanup_docx.py` 或类似临时脚本才能完成交付，先判断是否是正式 DSL 缺能力。除一次性诊断外，不得把临时 cleanup 作为交付链路；应把能力沉淀到 `build_block_ops_from_model.py` / `patch_docx_blocks.py`，并增加回归验证。

## 表格替换

- 替换表格时复用模板表格结构、边框、表头、重复表头、caption 和 Note 位置。
- 不得把 Pin Description、Electrical Characteristics、Order Information、Absolute Maximum Ratings 等强结构化表格降级为用空格或 tab 对齐的普通段落。
- 行数增加后必须检查跨页可读性、表头重复、Notes 邻近关系和列宽。
- 参数表优先使用状态列、source 列或脚注承载 `DS_*`，避免 inline 标注撑宽表格。

## 图片与视觉对象

- 替换图片或图表时复用原模板图片框、caption 和邻近说明。
- 没有新资产时保留占位容器并标 `DS_PLACEHOLDER_IMAGE`，不能直接删除导致资源坍塌。
- 只有旧模板示例图、错误 pinout、旧公司主体图或已被新资产替代的图，才允许 `preserve_visuals: false`。
- 删除视觉对象后必须通过模板保真和视觉检查解释资源减少。
- header/footer/cover 中的旧公司 Logo 或旧视觉主体不属于 block ops 的正文范围；应在 Stage-1 使用 `patch_docx_text.py --remove-visual-part word/headerN.xml` 这类显式 part 级操作，并写入 `asset-diff.json`。

## Pin Configuration 专项

生成 `PIN CONFIGURATION` 和 `PIN DESCRIPTION` 时：

- 从 `structured_sections.pins` 生成，不从模板示例残留推断。
- 目标为 16-pin VQFN / RGT 等封装时，生成 top-view 占位表或图，并标 `DS_COMPETITOR_REF`、`DS_PLACEHOLDER_IMAGE`、`DS_NEED_CONFIRM`。
- 必须删除或替换与目标封装冲突的旧 DFN / SOT / CSP / BST / FB 示例图、旧 pin 表和旧说明。
- `PIN CONFIGURATION` 与 `PIN DESCRIPTION` 必须使用同一 pin 数据源。
- DAP / Thermal Pad / Exposed Pad 必须出现在图、表或 Note 中。

## 受控插入

只允许在已识别锚点后插入：

- 差异标注清单。
- 待确认问题清单。
- 额外参数块。
- 占位图 / 占位表。
- 用户明确要求的新章节。

插入内容必须继承邻近样式，并进入内容长度与排版漂移检查。不得把调试说明随意追加到文末，破坏 Important Notice、Package、Mechanical、Tape & Reel 或支持页。

## 回归要求

修改 block ops 或 patch 脚本后，至少跑：

```powershell
py -m py_compile skills\ncs-datasheet-gen\scripts\build_block_ops_from_model.py skills\ncs-datasheet-gen\scripts\patch_docx_blocks.py
py skills\ncs-datasheet-gen\scripts\build_block_ops_from_model.py --model datasheet_model.normalized.json --output block-ops.json
py skills\ncs-datasheet-gen\scripts\patch_docx_blocks.py --template stage1.docx --operations block-ops.json --output stage2.docx --report block-patch-report.json --require-source-slots
py skills\ncs-datasheet-gen\scripts\check_docx_template_fidelity.py --template template.docx --output stage2.docx --asset-diff asset-diff.json --format json
```

还要静态检查生成脚本不得硬编码本轮样例型号、竞品型号或封装字符串；这些值必须来自 model 或 manifest。
