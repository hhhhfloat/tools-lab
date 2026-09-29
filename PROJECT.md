<!-- @anchor: tools_lab_project_intro -->
<!-- tools-lab：对 Agent 工作流工具做“黑盒行为验证”的实验项目 -->

<!-- @anchor: lab_positioning -->
## 项目定位
验证型实验项目：用真实工具（describe_anchors / build_anchor_index / read_between_anchors / insert_at_anchor / delete_between_anchors / get_file_structure）驱动多语言语料，记录「预期行为 vs 实测行为」，形成可复现的锚点工具测试基线与差异台账。被测工具的只读源码副本位于 `workflow-read-only/`，本 lab 不修改、不编译、不依赖其产物。

<!-- @anchor: lab_structure -->
## 整体结构
- `samples/`：多语言语料（每文件首个锚点为 `*_intro`），覆盖正常与边界写法；`samples/probe/` 为结构解析最小化探针。
- `samples/pkg_inner/dist/`、`samples/dist_named.js`、`samples/build_here/`：排除目录「段精确匹配」语义探针（应排除 / 应收录 / 应收录）。
- `probe/`：索引排除目录探针（node_modules / target / dist / `__pycache__` / src / deep/nested）、区间编辑往返（`probe/edit_roundtrip.js`、`probe/v3_edit_probe.js`）、相邻端点（`probe/adjacent_probe.js`）、安全扫描误报（`probe/security/`）。
- `dup/`、`dup2/`：同名文件 + 同名锚点，用于消歧与歧义报错测试。
- `samples/end_rule_a.js`、`samples/edit_target.js`：命名规则与区间编辑的专用探针。
- `harness/anchor_oracle.py`：独立实现的锚点扫描参照器 + 差分校验器（排除目录规格、两份索引文件集一致性、D1 与 D2 回归哨兵），输出落盘 `lab-out/oracle-report.txt`。
- `harness/js_strip_probe.py`：JS 解析器「旧步长 2 / 新步长 1」双向探针 + 工具侧 symbol 证据（`D2_FIXED`）。
- `lab-out/oracle-report.txt`：校验器落盘的报告（每次运行覆盖）。
- `UPDATE.md`：测试记录（只追加）。

<!-- @anchor: lab_method -->
## 关键决策
- **黑盒驱动**：不改被测源码，全部通过工具调用观察行为，任何 Agent 都能复现同一结论。
- **规格 oracle 差分**：把只读源码里的扫描规格（扩展名白名单、4 种注释风格正则、描述紧邻规则、文件内重名加 `_2`、排除目录段、点开头文件）独立重写为参照实现，再与工具产出的两份索引逐条比对，把“肉眼观察”变成可判定 PASS/CHECK 的自动对照。
- **回归哨兵**：已修复的差异不删白名单，而是改成“必须不再出现”的哨兵（`_end` 锚点缺于项目索引判 D1 回归；哨兵 JS/TS 文件失去全部 symbol 判 D2 回归）。
- **语料即断言**：语料注释统一以 `预期:` 开头写明期望结果，回归时按行核对。
- **报告落盘**：校验器用 Tee 把输出同时写入 `lab-out/oracle-report.txt`，避免证据只存在于一次对话里。
- **探针可复原**：编辑类探针（insert/delete）用完即用 `write_file` 写回基准内容，保证每轮回归起点一致。

<!-- @anchor: lab_conventions -->
## 规范约定
- 锚点 ID 一律 `<文件>_<模块>_<功能>`（小写+下划线），文件内唯一；需故意重名时用 `_dup` 命名。
- 描述注释必须紧贴锚点下一行，不留空行；块注释锚点只在同一行闭合时可用。
- 文档（本文件、UPDATE.md）内部不写锚点写法字面量，演示统一放 `samples/md_anchor_example.md`，避免污染索引。
- 校验器与探针输出统一用 ASCII 关键字 + UTF-8 输出流，规避 Windows 控制台编码问题。
- 编辑类用例一律用「专用探针文件 + 事后复原」，不直接改动既有语料。

<!-- @anchor: lab_findings -->
## 工具行为差异台账（D 系列 + 观察项；状态以 v3 回归为准）
### 已修复（v3 实测确认）
- **D1 已修** `_end` 后缀锚点同时进入两份索引，`.anchors.json` 与 `.project_index.json` 文件集完全一致。
- **D2 已修** JS/TS 结构解析恢复：`stripStringsOnly` 取字步长修为 1（转义成对跳过、字符串整体跳过）。`get_file_structure` 对 `.js`/`.ts`/`.mjs` 正常输出类/方法/顶层函数/锚点，JS 锚点 symbol 不再恒为 None。哨兵：`harness/anchor_oracle.py` 的 D2 SENTINEL + `harness/js_strip_probe.py` 的 `D2_FIXED=True`。
- **D3 已修** 索引复用 `SearchFileFilter.DEFAULT_EXCLUDED_DIRS`（24 个目录段，精确段匹配）并跳过点开头文件，与全文搜索口径一致。
- **D5 已修** describe 三态可区分：文件存在但无锚点 → 「文件存在，但未标注任何锚点」；目录存在但无锚点 → 「目录存在，但目录下没有锚点记录」；路径不存在 → 「不存在，或没有锚点记录」。
- **D7 已修** 源码含「锚点标记 + 反斜杠转义」（正则字面量）不再被误判为盘符路径；复测语料 `probe/security/traversal_recheck.py` 可正常写入并收录。

### 未修复 / 既有行为
- **D4 未修** 点路径不可写：`write_file` 拒绝 `.hidden/...`（提示文案已引导改用 describe_anchors / get_file_structure），故「点目录是否被索引排除」仍无法构造验证。
- **D6 未修** `compile_and_run(mode=java)` 在子目录推导出错主类名 → ClassNotFoundException；本 lab 统一用 Python 模式。
- **D8 既有行为** 文档/字符串里的锚点写法字面量会被收录（假阳性，描述为空）；演示固定在 `samples/md_anchor_example.md`，文档正文不写该字面量。

### 本轮新增观察（非缺陷，属既定实现口径）
- **B2 目录形提示词带尾斜杠不归一**：`file='samples'` 正常出概览（B1 已修），但 `file='samples/'` 落到「目录存在，但目录下没有锚点记录」——`matchesDir` 未做尾斜杠归一。规避：目录形写 `samples`。
- **目录形匹配偏宽松**：`file='probe'` 同时命中 `samples/probe/*`（匹配含 `contains("/" + dir + "/")`），概览会跨目录收录同名子目录。
- **索引刷新时机**：编辑类工具在同一轮内只即时刷新 `.anchors.json`（行号可用），`.project_index.json`（desc/symbol，describe 的数据源）在本轮结束时 flush；故同一轮内新建文件 describe 看不到、下一轮才可见。
- **结构视图的锚点清单与索引有差异**：`get_file_structure` 按「去字符串后的行」收集锚点（字符串内假锚点不出现），且不做同文件重名 `_2` 去重。
- **跨文件同名锚点在写/读路径报歧义**：`dup_same_shared` 因同时存在于 `dup/` 与 `dup2/` 而在未指定 `file` 时报错并列出候选。

<!-- @anchor: lab_run -->
## 运行方式
1. `build_anchor_index`（project_path=`tools-lab`）重建索引 → 生成 `.anchors.json` / `.project_index.json`。
2. `describe_anchors` 概览：全项目用 `file='.'`，目录用 `file='samples'`（不要带尾斜杠）；单文件传路径或仅文件名（重名时报歧义）。
3. 编辑类测试：`read_between_anchors` / `insert_at_anchor` / `delete_between_anchors`；写入后锚点行号即时刷新，描述/符号在本轮结束 flush，无需手动重建索引。
4. 差分校验：`compile_and_run`（mode=`python`）运行 `harness/anchor_oracle.py`，控制台输出 `RESULT=PASS/CHECK` 并写 `lab-out/oracle-report.txt`。
5. JS 结构回归：`compile_and_run`（mode=`python`）运行 `harness/js_strip_probe.py`，输出 `D2_FIXED=True`。
