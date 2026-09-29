<!-- @anchor: md_anchor_example_intro -->
<!-- 文档语料：验证 Markdown 中“引用锚点写法”的内联代码会被误当真实锚点收录 -->

# 锚点写法示例（含假阳性演示）

行内代码中的写法也会被收录：

- JS 风格示例：`// @anchor: mirror_js_style`
- Python 风格示例：`# @anchor: mirror_py_style`
- CSS 风格示例：`/* @anchor: mirror_css_style */`
- HTML 风格示例：`<!-- @anchor: mirror_html_style -->`

预期: 上面四行会被 `build_anchor_index` 收录（假阳性），且 id 会带 `mirror_*` 前缀。
