# Model Validation Rules

当你构建或校验 `datasheet_model.json` / `.yaml` 时，读取并执行本文件。模型校验失败时先修模型，不生成 DOCX。

## 必需结构

生成 `datasheet_model` 前必须已有通过校验的 `input-gate.json`。`input-gate.json` 只记录逐项门禁状态，不替代 `datasheet_model.metadata`；模型中仍要保留用户确认结果、来源和状态。

模型至少包含：

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
    placeholders:
    header_footer:
    legal_notice:
    toc:
    style_policy:
  slot_map:
    - slot:
      operation:
      target:
      source:
      status:
  semi_structured_sections:
  structured_sections:
  assets:
  markings:
```

`fixed_layout.template_manifest` 至少包含 `sections`、`headers_footers`、`toc_fields`、`page_roles`、`replaceable_blocks`、`anchors`、`sample_rows`、`protected_blocks` 和 `resource_inventory`。

`resource_inventory` 至少统计 `media_parts`、`drawing_objects`、`chart_parts`、`embedding_parts`、`comments`、`package_entries`、`sections`、`tables`、`paragraphs`、`toc_fields`、`field_chars` 和 `styles`。

## Source 与标注

- 强结构化条目必须带 `source`。
- 电气、时序、热、ESD、推荐工作条件等参数必须保留单位、min / typ / max、测试条件和来源。
- 无来源时不得填入正式值，只能占位并标 `DS_TBD` 或 `DS_NEED_CONFIRM`。
- 来自竞品且未被确认的参数必须标 `DS_COMPETITOR_REF` 和 / 或 `DS_UNVERIFIED_SPEC`。
- 历史产品低于竞品时，marked draft 默认写入竞品目标规格，同时标 `DS_BELOW_COMPETITOR`、`DS_UNVERIFIED_SPEC`、`DS_NEED_CONFIRM`。
- 历史缺失但竞品有时，marked draft 默认写入竞品目标内容或目标占位，同时标 `DS_COMPETITOR_REF`、`DS_MISSING_HISTORY`、`DS_NEED_CONFIRM`。
- clean 版只能包含已确认内容，或包含用户明确接受的剩余风险说明。
- 若输出偏好为 clean candidate，但模型仍含 `DS_NEED_CONFIRM`、`DS_COMPETITOR_REF`、`DS_UNVERIFIED_SPEC`、`DS_MISSING_HISTORY`、未授权竞品图或未确认法律文本，必须自动降级为 marked draft，或删除对应内容并获得用户接受。

## slot_map 校验

每个输出内容必须映射到 `slot_map`。每个 `slot_map` 条目必须说明：

- `slot`：稳定语义槽位，例如 `front.description`、`pins.pin_configuration`、`tables.electrical_characteristics`。
- `operation`：`fill`、`replace_block` 或 `insert_after_anchor`。
- `target`：来自 `template_manifest` 的锚点、段落、表格、占位符或受保护区域判断。
- `source`：用户输入、竞品、历史产品、结构化数据或生成说明。
- `status`：confirmed、target、draft、need_confirm、placeholder 等。

找不到目标槽位时，不生成 DOCX。不得让脚本随机选择位置追加内容。

## Pin / Package

必须检查：

- pin 编号是否重复。
- pin 编号是否连续，尤其是目标封装声明为 16-pin、24-pin 等时。
- pin name 是否冲突。
- pin type 是否合理。
- 电源、地、模拟输入、数字输入、输出、差分对、控制 pin 是否与目标兼容封装一致。
- `_P` / `_N` 差分对是否成对出现。
- DAP / Thermal Pad / Exposed Pad 的连接要求是否保留。
- `metadata.target_policy` 中的 pin-to-pin 目标、封装名和 pin 数是否与 `structured_sections.pins` 一致。
- `PIN CONFIGURATION` 与 `PIN DESCRIPTION` 使用同一目标 pin 数据，不能一个来自竞品、一个残留模板旧产品。

## 参数与表格

必须检查：

- min / typ / max 是否放在正确列。
- 单位是否存在且一致。
- 测试条件是否保留。
- Note / Notes 是否保留并靠近对应表格或参数块。
- ESD、thermal、recommended operating conditions、absolute maximum ratings 是否与电气参数边界一致。
- 竞品 typical value 不得改写成我司 guaranteed value。
- 历史与竞品测试条件不同时，必须标“测试条件不同，不能直接对比”或等价说明。
- 低于竞品、历史缺失、测试条件不可比的项必须进入 `markings`。

## Register Map

存在寄存器内容时，必须检查：

- 地址是否存在且格式一致。
- register address 是否重复。
- bit range 是否重叠或越界。
- reset value 是否存在。
- access type 是否存在并使用统一枚举。
- bit field、enum、interrupt status / mask / clear 关系是否可追踪。
- 无来源的寄存器地址、reset value 或 bit 定义不得生成正式值。

## Assets

必须检查：

- `assets` 中的本地文件路径是否存在。
- 竞品图片是否被标为竞品参考、待授权或待重绘。
- 占位图片是否标 `DS_PLACEHOLDER_IMAGE`。
- release / clean 版不得保留未授权竞品截图或图片。
- block diagram、pinout、package drawing、typical application、test configuration、typical curves 等图类资产必须有来源和替换策略。

## 文档后校验

生成 DOCX 后必须检查：

- 模板保真是否失败。
- 未替换占位符。
- TODO / TBD / FIXME / 内部注释残留。
- 旧模板示例内容。
- 未授权竞品图片。
- 表格超宽、图片越界、孤立标题、空白页异常。
- 目录未更新、图号 / 表号错误、页眉页脚错误。
- 醒目标注清单未处理。
- `DS_*` 标记被拉散、截断、省略号化或挤破表格。
- marked draft 中正文 inline `DS_*` 过多导致阅读困难时，改为状态列、source 列、脚注或集中标注；不得通过缩小字体硬塞。
- clean candidate 中残留未确认 `DS_*` 时，文档状态必须降级为 marked draft。

模型报告可写入 `model-validation.json`，文档报告可写入 `document-check.json`。报告结论只能基于实际执行的检查。
