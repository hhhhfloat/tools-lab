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
- `search/`：search_text 语料 —— 跨文件符号（`lib/alpha|beta|gamma` + `app.js`）、同名文件（`dup/`、`dup2/`）、超长行（`long_line.txt`）、正则特殊字符（`regex_probe.txt`）、30 条上限（`many.txt`）、白名单外扩展名（`ext_samples/{notes.log,legacy.c,module.mjs,plain}`）、排除目录（`dist/excluded.js`）、删除探针（`delete_me.js`、`del_dir/`、`idx_stale.js`）。
- `probe/`：索引排除目录探针、区间编辑往返、相邻端点、安全扫描误报；`probe/io/` 为 IO 探针（截断 `mid_probe.txt`/`trunc_probe.txt`、0 字节、无结尾换行、CRLF、多级目录、反斜杠、尾斜杠、点路径）；`probe/dist/io2_probe.js` 为写排除目录探针。
- `dup/`、`dup2/`：同名文件 + 同名锚点，用于消歧与歧义报错。
- `harness/anchor_oracle.py`：锚点扫描参照器 + 两份索引差分（含 D1/D2 哨兵），报告 `lab-out/oracle-report.txt`。
- `harness/io_oracle.py`：read_file / write_file / delete_file 规格抽取 + 实测基线 + 自动校验，报告 `lab-out/io-report.txt`。
- `harness/search_oracle.py`：search_text 规格抽取 + 独立重实现 + 转录差分 + 不变量校验，报告 `lab-out/search-report.txt`。
- `harness/index_snapshot.py`：两份索引文件集快照（D1 哨兵），供 io-02 / del-01 取证。
- `harness/js_strip_probe.py`：JS 取字算法「旧步长 2 / 新步长 1」双向探针。
- `tmp/`：一次性分析脚本（约定不写锚点字面量，不污染索引）。
- `lab-out/`：校验器落盘报告（每次运行覆盖）。
- `UPDATE.md`：测试记录（只追加）。



<!-- @anchor: lab_method -->
## 关键决策
- **黑盒驱动**：不改被测源码，全部通过工具调用观察行为，任何 Agent 都能复现同一结论。
- **规格 oracle 差分**：把只读源码里的规格（扩展名白名单、4 种注释风格正则、描述紧邻规则、重名加 `_2`、排除目录段、点开头文件、search 的 30 条上限与预览截断）独立重写为参照实现，再与工具产出的索引 / 输出逐条比对，把「肉眼观察」变成可判定 PASS/CHECK 的自动对照。
- **规格抽取**：`io_oracle` / `search_oracle` 用正则从 FileOperator / ToolExecutor / ToolDefinitions / AnchorIndex / TextSearcher / SearchFileFilter 抽常量、方法体特征与消息模板（不执行源码），与实测基线、沙箱事实比对；schema 描述与实现不符同样计为差异。
- **索引链路哨兵**：D1 哨兵要求 `.anchors.json` 与 `.project_index.json` 文件集一致；io-02b / del-01 都用「写排除目录 / 删文件后两份索引是否偏差」观察刷新链路。
- **回归哨兵**：已修复项改成「必须不再出现」的断言（C2 io-01 阈值相等、D1 文件集一致、JS 必带 symbol、`tmp/` 不得进索引）。
- **冻结项哨兵**：已知未修项用「必须仍然如此」的冻结断言（C14 io-02b、C15 del-01），一旦被修复该条会 FAIL 以提醒更新台账。
- **语料即断言**：语料注释统一以 `预期:` 开头写明期望结果。
- **报告落盘**：四个校验器都用 Tee 同时写 `lab-out/`，避免证据只存在于一次对话里。
- **探针可复原**：编辑 / 删除类探针用完即写回基准内容。
- **关键词防自命中**：校验器需要搜索某个「只在语料里出现」的 token 时，用相邻字符串隐式拼接，避免校验器自身源码命中该 token。



<!-- @anchor: lab_conventions -->
## 规范约定
- 锚点 ID 一律 `<文件>_<模块>_<功能>`（小写+下划线），文件内唯一；需故意重名时用 `_dup` 命名。
- 描述注释必须紧贴锚点下一行，不留空行；块注释锚点只在同一行闭合时可用。
- 文档正文、`tmp/` 脚本、harness 自身一律不写锚点写法字面量（需要时用 `"@"+"anchor"` 拼接或 `anchor-id:` 前缀），避免污染索引（io_oracle C9 哨兵）。
- 校验器与探针输出统一用 ASCII 关键字 + UTF-8 输出流（`sys.stdout.reconfigure`）；个别字符在 GBK 控制台可能显示为乱码，以落盘报告为准。
- 编辑类用例一律用「专用探针文件 + 事后复原」，不直接改动既有语料。
- 素材类内容（长文本、图集数据等用户提供物）不修改。


<!-- @anchor: lab_findings -->
## 工具行为差异台账（状态以 v5 回归为准）
### 已修复（v3/v4 确认，v5 保持）
- **D1 已修** `_end` 后缀锚点同时进入两份索引；rebuild 后两份索引文件集一致。
- **D2 已修** JS/TS 结构解析恢复，symbol 正常输出（哨兵见两个 oracle）。
- **D3 已修** 索引复用 `SearchFileFilter.DEFAULT_EXCLUDED_DIRS`（24 段精确匹配）并跳过点开头文件。
- **D5 已修** describe 三态可区分：文件无锚点 / 目录无锚点 / 路径不存在。
- **D7 已修** 含「锚点标记 + 反斜杠」的正则字面量不再被误判为盘符路径。
- **io-01 已修** `read_file` 描述阈值已改为 50000，与实现 `MAX_LENGTH=50000` 一致（C2 哨兵）；实测 5247 字符文件完整返回。
### 部分修复 / 未修
- **io-02 部分修（拆出 io-02b）** `write_file` 的**即时**刷新（`AnchorIndex.refreshAnchorsFile`）已套 `isExcludedDir`：写 `probe/dist/` 后 `.anchors.json` 不再收录；但**轮末** flush 走的 `refreshProjectIndexFile` 未套排除规则，`.project_index.json` 仍收录 → 两份索引文件集偏差（实测 `only_P=['probe/dist/io2_probe.js']`、`D1_CONSISTENT=False`），需 `build_anchor_index` 才收敛。冻结断言 C14。
- **del-01 未修** `delete_file` 未接入索引刷新：`ToolExecutor.dispatch` 的 `delete_file` 分支不调用 `markDirtyByFilename`（写文件分支有）→ 删除带锚点文件后两份索引均残留条目直到 rebuild。冻结断言 C15。
- **sc-01 未修（检索口径）** `TextSearcher.searchText` 的 `matchCount` 只在结果真正加入时自增，故 `total > shown` 的「仅显示前 30 条」分支恒不触发：命中 41 条时只报「🔍 找到 30 条匹配结果：」，无法察觉被截断，与工具描述「超出会提示缩小范围」不符。
- **D4 未修** 点开头路径一律拒绝（read / write / delete 同一文案）；索引侧「点目录是否被排除」仍无法构造，读索引走 Python 侧。
- **D6 改记** java 模式主类名按文件名推导、不解析源码：`Sub.java` 内含非 public 类时报 CNFE。
- **D8 既有** 文档 / 字符串里的锚点写法字面量被收录（假阳性、desc 为空）。
### v5 复核确认（仍存在，属既定口径）
- **B2 尾斜杠不归一**：`describe_anchors(file='samples/')` 落到「目录存在，但目录下没有锚点记录」；`write_file` 尾斜杠被 Path 归一化。规避：目录形不带尾斜杠。
- **目录形匹配偏宽松**：`file='probe'` 连带收录 `samples/probe/*`。
- **索引刷新时机**：同轮 `.anchors.json` 即时更新、`.project_index.json` 轮末 flush。
- **跨文件同名锚点报歧义**：`file='Same.java'` 列出 `dup/Same.java`、`dup2/Same.java`。
- **结构视图口径差异**：`get_file_structure(app.js)` 不列字符串内假锚点、不做同文件重名 `_2` 去重。
### search_text 口径（v5 实测）
- keyword 按 Java 正则编译：`a.b` 命中 a+b / a.b / aXb，`pipe|alt` 生效，默认区分大小写；非法正则回「关键词正则表达式错误: …」；空 / `.` path 时输出路径带 `tools-lab/` 前缀。
- file_pattern 走 `fileName.endsWith` / 扩展名比对：`*.js`、`.js`、`js,py`、`plain` 均可用；默认白名单 26 项（含 `.js/.txt/.py`，不含 `.log/.c/.mjs`），可用 file_pattern 越过白名单搜 `.log` 等。
- 排除目录（24 段）与排除文件（`.anchors.json` / `.project_index.json` / `.agent_entry.json` 等）不参与搜索；预览 = `line.trim()` 截前 80 字符 + `...`。
- 上限 30 条，被截断时**总数也被截为 30**（sc-01）。
### delete_file 口径（v5 实测）
- 成功 `✅ 已删除文件: X`；不存在 `文件不存在: X`；目录 `⚠️ 不能删除目录，请仅删除单个文件…`；`UPDATE.md` `❌ UPDATE.md 不允许删除。`；点开头路径与含两边点号的路径按 checkPath 拒绝。
- 删除**不**触发索引刷新（del-01），带锚点文件删除后两份索引残留，需 `build_anchor_index`。



<!-- @anchor: lab_io -->
<!-- read_file / write_file / delete_file / search_text 实测口径（v5），供后续用例参照 -->
## IO 与检索类工具实测口径（v5）
### read_file / write_file（同 v4；io-01 已修）
- `read_file` 正常：`📄 文件 <name> 内容已阅读` + 原文（原样输出，不补 / 不剪换行）；0 字节文件只回头部。
- `read_file` 缺失 / 目录 / 目录带尾斜杠：统一 `文件不存在或是一个目录: <name>`。
- `read_file` 超阈值：截断到 50000（UTF-16）并附 `... [文件过长，已截断。如需完整内容请告知]`。
- `read_file` 名为 `UPDATE.md`：拒绝并提示改用 `read_between_anchors`（`delete_file` 对其同样拒绝）。
- `read_file` / `write_file` / `delete_file` 点开头路径：拒绝并引导 `describe_anchors` / `get_file_structure`。
- `write_file` 成功：`✅ <filename>`；自动创建多级父目录；整文件覆盖；逐字写入（不补结尾换行、CRLF 不归一化）；名字含反斜杠按路径分隔符处理；尾斜杠 + 不存在时落成同名普通文件。
- `write_file` 失败（目标是目录 / 父路径是文件）：`写入文件失败: <绝对路径或 src -> dst>`（消息含沙箱绝对路径，注意不要外传）。
- 提示：Python 侧 `Path.write_text` 在 Windows 会把 `\n` 写成 `\r\n`（`probe/io/mid_probe.txt` 磁盘 5300 / 内存 5247 UTF-16），核对字符数一律以 `java_len`（UTF-16）为准。
### delete_file（v5 新增）
- 见台账「delete_file 口径」。探针 `search/delete_me.js`、`search/del_dir/` 用完即复原；删除不刷新索引（del-01）。
### search_text（v5 新增）
- 见台账「search_text 口径」。`file_pattern` 传 `.*` / 空 视为不限制。
### 复现命令（`compile_and_run`，mode=`python`）
1. 先 `build_anchor_index { project_path: "tools-lab" }` —— 否则 C7/C8 会因未收敛的索引偏差 FAIL。
2. `tools-lab/harness/io_oracle.py` → `RESULT=PASS`（含 io-01 哨兵 C2、冻结项 C14/C15），写 `lab-out/io-report.txt`。
3. `tools-lab/harness/search_oracle.py` → `RESULT=PASS`（17 转录差分 + 9 不变量），写 `lab-out/search-report.txt`。
4. `tools-lab/harness/anchor_oracle.py` → 锚点基线回归（item diffs=0）。
5. `tools-lab/harness/index_snapshot.py` → 观察 `D1_CONSISTENT` / `only_A` / `only_P`。



<!-- @anchor: lab_run -->
## 运行方式
1. `build_anchor_index`（project_path=`tools-lab`）重建索引 → 生成 `.anchors.json` / `.project_index.json`。
2. `describe_anchors` 概览：全项目用 `file='.'`，目录用 `file='samples'`（不要带尾斜杠）；单文件传路径或仅文件名（重名时报歧义）。
3. 编辑类测试：`read_between_anchors` / `insert_at_anchor` / `delete_between_anchors`；写入后锚点行号即时刷新，描述/符号在本轮结束 flush，无需手动重建索引。
4. 差分校验：`compile_and_run`（mode=`python`）运行 `harness/anchor_oracle.py`，控制台输出 `RESULT=PASS/CHECK` 并写 `lab-out/oracle-report.txt`。
5. JS 结构回归：`compile_and_run`（mode=`python`）运行 `harness/js_strip_probe.py`，输出 `D2_FIXED=True`。
