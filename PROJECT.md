<!-- @anchor: tools_lab_project_intro -->
<!-- tools-lab：对 Agent 工作流工具做“黑盒行为验证”的实验项目 -->

<!-- @anchor: lab_positioning -->
## 项目定位
验证型实验项目：用真实工具驱动多语言语料，记录「预期行为 vs 实测行为」，形成可复现的测试基线与差异台账。
- 锚点工具组：`describe_anchors` / `build_anchor_index` / `read_between_anchors` / `insert_at_anchor` / `delete_between_anchors` / `get_file_structure`。
- IO 工具组：`read_file` / `write_file`（v4 起纳入验证）。
被测工具的只读源码副本位于 `workflow-read-only/`，本 lab 不修改、不编译、不依赖其产物；源码只用于抽取规格（正则读取常量与消息模板）。


<!-- @anchor: lab_structure -->
## 整体结构
- `samples/`：多语言语料（每文件首个锚点为 `*_intro`）；`samples/probe/` 结构解析最小化探针；`samples/long-text.log` 为 80k 字符无锚点长文本（read_file 截断用例）。
- `probe/`：索引排除目录探针、区间编辑往返、相邻端点、安全扫描误报；`probe/io/` 为 IO 行为探针（截断、0 字节、无结尾换行、CRLF、多级目录、反斜杠、尾斜杠、缺失/目录/点路径）。
- `dup/`、`dup2/`：同名文件 + 同名锚点，用于消歧与歧义报错。
- `harness/anchor_oracle.py`：锚点扫描参照器 + 两份索引差分（含 D1/D2 哨兵），报告 `lab-out/oracle-report.txt`。
- `harness/io_oracle.py`：read_file/write_file 规格抽取 + 实测基线 + 12 条自动校验，报告 `lab-out/io-report.txt`。
- `harness/js_strip_probe.py`：JS 取字算法「旧步长 2 / 新步长 1」双向探针。
- `tmp/`：一次性分析脚本（去锚点化，不污染索引）。
- `lab-out/`：校验器落盘报告（每次运行覆盖）。
- `UPDATE.md`：测试记录（只追加）。


<!-- @anchor: lab_method -->
## 关键决策
- **黑盒驱动**：不改被测源码，全部通过工具调用观察行为，任何 Agent 都能复现同一结论。
- **规格 oracle 差分**：把只读源码里的扫描规格（扩展名白名单、4 种注释风格正则、描述紧邻规则、文件内重名加 `_2`、排除目录段、点开头文件）独立重写为参照实现，再与工具产出的两份索引逐条比对，把「肉眼观察」变成可判定 PASS/CHECK 的自动对照。
- **IO 规格抽取**：`io_oracle` 用正则从 FileOperator / ToolExecutor / ToolDefinitions 抽常量与消息模板（不执行源码），与实测基线、沙箱事实比对；schema 描述与实现不符同样计为差异（io-01）。
- **回归哨兵**：已修复的差异不删白名单，而是改成「必须不再出现」的哨兵（两份索引文件集一致 = D1；哨兵 JS/TS 必须带 symbol = D2；`tmp/` 不得进索引 = C9）。
- **语料即断言**：语料注释统一以 `预期:` 开头写明期望结果。
- **报告落盘**：两个校验器都用 Tee 同时写 `lab-out/`，避免证据只存在于一次对话里。
- **探针可复原**：编辑类探针用完即用 `write_file` 写回基准内容。


<!-- @anchor: lab_conventions -->
## 规范约定
- 锚点 ID 一律 `<文件>_<模块>_<功能>`（小写+下划线），文件内唯一；需故意重名时用 `_dup` 命名。
- 描述注释必须紧贴锚点下一行，不留空行；块注释锚点只在同一行闭合时可用。
- 文档正文、`tmp/` 脚本、harness 自身一律不写锚点写法字面量（需要时用 `"@"+"anchor"` 拼接或 `anchor-id:` 前缀），避免污染索引（io_oracle C9 哨兵）。
- 校验器与探针输出统一用 ASCII 关键字 + UTF-8 输出流（`sys.stdout.reconfigure`）；个别字符在 GBK 控制台可能显示为乱码，以落盘报告为准。
- 编辑类用例一律用「专用探针文件 + 事后复原」，不直接改动既有语料。
- 素材类内容（长文本、图集数据等用户提供物）不修改。


<!-- @anchor: lab_findings -->
## 工具行为差异台账（状态以 v4 回归为准）
### 已修复（v3 实测确认，v4 保持）
- **D1 已修** `_end` 后缀锚点同时进入两份索引，文件集一致（v4 复核 42/42 一致）。
- **D2 已修** JS/TS 结构解析恢复，symbol 正常输出；哨兵见两个 oracle。
- **D3 已修** 索引复用 `SearchFileFilter.DEFAULT_EXCLUDED_DIRS`（24 段精确匹配）并跳过点开头文件。
- **D5 已修** describe 三态可区分：文件无锚点 / 目录无锚点 / 路径不存在。
- **D7 已修** 含「锚点标记 + 反斜杠」的正则字面量不再被误判为盘符路径。
### 未修复 / 既有行为
- **D4 未修** 点开头路径一律拒绝（`read_file` / `write_file` / `delete_file` 同一文案），故「点目录是否被索引排除」仍无法构造；要看索引请用 Python 侧读取。
- **D6 部分改记（v4 复核）** java 模式在根目录 / 子目录 / 子目录 + `package` 三种形态均运行成功，原「子目录必失败（CNFE）」未复现；剩余限制是**主类名按文件名推导、不解析源码**：文件名与主类名不一致时（`probe/java_sub/Sub.java` 内为非 public 类 `Other`）报 `ClassNotFoundException: Sub`。对照探针 `probe/java_sub/{Hello,Sub}.java`。
- **D8 既有行为** 文档/字符串里的锚点写法字面量被收录（假阳性、desc 为空）；v4 复核仍存在（`samples/md_anchor_example.md` 的 4 个 `mirror_*`）。
### v4 新增（IO 行为）
- **io-01 描述与实现不符** `read_file` 的 schema 描述写「限制 5000 字符」，实现是 `MAX_LENGTH=50000`（UTF-16 计数）。实测：13775 字符文件完整返回、81843 字符文件在 java≈50000 处截断并附标准提示。
- **io-02 即时刷新绕过排除规则** `write_file` 触发的索引刷新不套用排除目录过滤，写入 `probe/dist/` 的文件会进两份索引，直到 `build_anchor_index` 重建才清理。规避：写完排除目录后补一次 rebuild。
### v4 复核确认（仍存在，属既定口径）
- **B2 尾斜杠不归一**：`describe_anchors(file='samples/')` → 「目录存在，但目录下没有锚点记录」；`write_file(".../dir_target/")` → 落成名为 `dir_target` 的普通文件。规避：目录形不带尾斜杠。
- **目录形匹配偏宽松**：`file='probe'` 会连带收录 `samples/probe/*`（`contains("/"+dir+"/")`）。
- **索引刷新时机**：同轮内 `.anchors.json` 即时更新、`.project_index.json` 轮末 flush；同轮 describe 新文件 → 「文件存在，但未标注任何锚点」，下一轮可见且带 symbol（C10 哨兵）。
- **跨文件同名锚点报歧义**：`file='Same.java'` 报歧义并列出 `dup/Same.java`、`dup2/Same.java`。
- **结构视图口径差异**：`get_file_structure(samples/app.js)` 列 8 条锚点 —— 字符串内假锚点不出现、同文件重名不做 `_2` 去重（两处均为 `app_js_dup`），与索引（9 条、含 `app_js_fake_in_string` / `app_js_dup_2`）不同口径。


<!-- @anchor: lab_io -->
<!-- read_file / write_file 实测口径（v4），供后续用例参照 -->
## read_file / write_file 实测口径
- `read_file` 正常：`📄 文件 <name> 内容已阅读` + 原文（原样输出，不补/不剪换行）；0 字节文件只回头部。
- `read_file` 缺失 / 目录 / 目录带尾斜杠：统一 `文件不存在或是一个目录: <name>`。
- `read_file` 超阈值：截断到 50000（UTF-16）并附 `\n... [文件过长，已截断。如需完整内容请告知]`。
- `read_file` 名为 `UPDATE.md`：拒绝并提示改用 `read_between_anchors`（`delete_file` 对其同样拒绝）。
- `read_file` / `write_file` 点开头路径：拒绝并引导 `describe_anchors` / `get_file_structure`。
- `write_file` 成功：`✅ <filename>`；自动创建多级父目录；整文件覆盖；逐字写入（不补结尾换行、CRLF 不归一化）。
- `write_file` 名字含反斜杠：按路径分隔符处理（生成子目录）；路径带尾斜杠且不存在时：落成同名普通文件。
- `write_file` 失败（目标是目录 / 父路径是文件）：`写入文件失败: <绝对路径或 src -> dst>`（消息含沙箱绝对路径，注意不要外传）。
- 补充运行方式：第 6 步 IO 差分校验 —— `compile_and_run`（mode=`python`）运行 `harness/io_oracle.py`，输出 `RESULT=PASS` 并写 `lab-out/io-report.txt`。


<!-- @anchor: lab_run -->
## 运行方式
1. `build_anchor_index`（project_path=`tools-lab`）重建索引 → 生成 `.anchors.json` / `.project_index.json`。
2. `describe_anchors` 概览：全项目用 `file='.'`，目录用 `file='samples'`（不要带尾斜杠）；单文件传路径或仅文件名（重名时报歧义）。
3. 编辑类测试：`read_between_anchors` / `insert_at_anchor` / `delete_between_anchors`；写入后锚点行号即时刷新，描述/符号在本轮结束 flush，无需手动重建索引。
4. 差分校验：`compile_and_run`（mode=`python`）运行 `harness/anchor_oracle.py`，控制台输出 `RESULT=PASS/CHECK` 并写 `lab-out/oracle-report.txt`。
5. JS 结构回归：`compile_and_run`（mode=`python`）运行 `harness/js_strip_probe.py`，输出 `D2_FIXED=True`。
