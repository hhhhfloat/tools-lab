<!-- @anchor: tools_lab_update_intro -->
<!-- tools-lab 测试更新记录：仅追加，不修改历史条目 -->

## [v1] 锚点操作工具黑盒测试基线（37 文件 / 114 锚点）
- 步骤：1) lab 骨架 2) 多语言语料 3) 扫描类工具 4) 区间编辑工具 5) 结构解析工具 6) 独立差分校验器 7) 结论汇总（全部完成）
- 校验器：`harness/anchor_oracle.py`（Python 运行模式）按只读源码规格独立重写「白名单 + 正则 + 描述提取 + 重名后缀」，读取 `.anchors.json` / `.project_index.json` 逐条差分，输出落盘 `lab-out/oracle-report.txt`。
- 总体结论：文件级 37/37 一致，id/line/desc 逐条零差异；唯一已知差异为 `_end` 后缀锚点不进项目索引（D1）。

### 用例矩阵与实测
| # | 用例 | 预期 | 实测 |
|---|------|------|------|
| 1 | 4 种注释风格（行注释 / `#` / 块注释 / HTML 注释）覆盖 java,py,js,ts,cpp,h,css,html,md,xml,json,yaml,sh,sql,properties,txt | 全部收录 | ✅ 全部收录，id/行号/描述与参照实现一致 |
| 2 | 白名单外扩展名 `.c` / `.kt` / `.mjs` | 不收录 | ✅ 未出现在索引（`.mjs` 虽有 JS 解析器但不扫描锚点） |
| 3 | 描述紧邻锚点下一行（`//`、`#`、`/* */`、`<!-- -->`） | 提取为描述 | ✅ 与参照实现一致 |
| 4 | 锚点下一行为空行 / 非注释 | 描述为空 | ✅ 显示「（无描述）」 |
| 5 | 同文件重复 id | 第二次起改名 `_2` | ✅ `app_java_dup` / `app_java_dup_2` |
| 6 | 多行块注释写法（`/**` 换行 + `* 锚点`） | 不收录 | ✅ 未收录 |
| 7 | 字符串字面量内出现锚点写法（py/js/json） | 参照实现也收录（假阳性） | ✅ 收录且描述为空，两者一致 |
| 8 | md 内联代码中引用锚点写法 | 假阳性 | ✅ 收录为 `mirror_*` 4 条 |
| 9 | SQL `--` 注释锚点 vs 块注释锚点 | `--` 不收录、块注释收录 | ✅ 实测一致 |
| 10 | 目录模式 describe（`samples`） | 输出 `_intro` 概览计数 | ✅ 15/17 已标注，无 `_intro` 的文件单列 |
| 11 | 文件模式 describe：全路径 / 仅文件名后缀匹配 | 均可命中 | ✅ `samples/README.md` 与 `README.md` 等价 |
| 12 | 同名文件歧义（`Same.java`） | 报错并列出候选 | ✅ 列出 `dup/Same.java`、`dup2/Same.java` |
| 13 | describe 不存在的路径 / 无锚点文件 | 应可区分 | ⚠ 均返回「下没有锚点记录」（D5） |
| 14 | read_between：同文件区间 | 输出含两端锚点及行号 | ✅ 行号与实际一致 |
| 15 | read_between：跨文件 / 反序 / 未知 id / 无 file 但重名 | 分类报错 | ✅ 4 类错误均按预期文案返回 |
| 16 | insert_at_anchor：before / after | 在锚点上下插入并保留锚点 | ✅ 多行内容原样写入 |
| 17 | insert_at_anchor：非法 position / 未知 id / 重名无 file | 报错 | ✅ 三种错误均按预期返回 |
| 18 | 插入后同一轮 describe 是否可见 | 需能立刻看到新锚点 | ✅ 立即可见（行号与描述同步，编辑轮结束会 flush） |
| 19 | delete_between：正常区间 | 删除中间行并报数量 | ✅ 报「已删除 5 行代码」 |
| 20 | delete_between：相邻锚点 / 同一锚点 / 跨文件 | 告警或报错 | ✅ 分别返回「没有内容可删除」「起始锚点必须在结束锚点之前」「不在同一个文件中」 |
| 21 | 索引排除目录探针（target、dist、node_modules、`__pycache__`、deep/nested、src） | 与全文搜索的排除集一致 | ⚠ 全部被收录，索引侧未套用排除目录（D3） |
| 22 | 点目录探针（`.git`、`.hidden`） | 验证是否排除 | ⚠ `write_file` 直接拒绝点目录写入，无法构造（D4） |
| 23 | get_file_structure：java / py / cpp / h / css / html / 未知扩展名 | 输出类/方法/字段/锚点 | ✅ 均正常（未知扩展名走兜底，仅语言+锚点） |
| 24 | get_file_structure：js / ts / mjs | 输出 JS 结构与锚点 | ❌ 仅输出「语言: JavaScript」，无任何分区（D2） |
| 25 | get_file_structure：`.md` | 转发 describe_anchors | ✅ 返回锚点清单（Markdown 格式） |
| 26 | 符号归属 | 锚点归属其所在/最近方法 | ✅ 规律符合实现：方法上方锚点归属该方法，体内锚点归属其后最近方法（Python 方法 start==end） |

### 差异与问题清单
- **D1 `_end` 后缀锚点不进项目索引**：`edit_target_scratch_end`、`end_rule_a_probe_end` 在 `.anchors.json` 中存在（read/insert/delete 可用），但 `.project_index.json` 缺失 → `describe_anchors` 不展示；`_end` 出现在中间（`end_rule_a_end_middle`）不受影响。
- **D2 JS/TS 结构解析为空**：`get_file_structure` 对 `.js/.ts/.mjs` 只回显语言，最小文件（无字符串、无花括号）同样为空；连带 `describe_anchors` 中 JS 锚点 symbol 全为 None。
- **D3 索引未套用排除目录**：`target`、`dist`、`node_modules`、`__pycache__` 等仍被 `build_anchor_index` 收录，与 `SearchFileFilter` 的默认排除集不一致。
- **D4 点路径不可写**：`write_file` 拒绝任何含点号目录/文件的路径（`.git/`、`.hidden/`），故跳过目录的排除行为无法在此环境验证。
- **D5 describe 无法区分「文件不存在」与「文件无锚点」**：两条路径返回同一句提示。
- **D6 Java 单文件运行模式在子目录失效**：`compile_and_run(mode=java)` 对 `tools-lab/harness/X.java` 推导主类名为 `tools-lab.harness.X` → ClassNotFoundException；本 lab 改用 Python 模式（探针 `harness/hello_probe.py` 已验证可用）。
- **D7 安全扫描误伤锚点正则**：源码里出现「锚点标记 + 反斜杠」（如正则中的 `@anchor:\\s*`）被判为 `FILE_PATH_TRAVERSAL`（误认盘符 `r:\`），需把标记拆成常量拼接（已在 harness 中规避）。
- **D8 文档自身会被假锚点污染**：PROJECT.md 早期版本里写的「块注释锚点写法示例」被收录成 `x`、`x_2`，已改写措辞；演示统一放在 `samples/md_anchor_example.md`。

### 复现方式
1. `build_anchor_index { project_path: "tools-lab" }`
2. `compile_and_run { filename: "tools-lab/harness/anchor_oracle.py", mode: "python" }` → 控制台输出 + `lab-out/oracle-report.txt`


## [v1.1] 校验器收口与基线固化
- 校验器新增已知差异白名单（`oracle_known_diffs`）：`_end` 后缀锚点缺失于项目索引计入 KNOWN-D1，不再拉低判定。
- 最终状态：`oracle files=36, item diffs=0, known diffs=2, file-level problems=0` → `RESULT=PASS`，报告落盘 `lab-out/oracle-report.txt`。
- 回归方式：`build_anchor_index(tools-lab)` → 运行 `harness/anchor_oracle.py`；语料本身的期望写在各文件注释的 `预期:` 行。
- 语料规模快照：java/js/ts/css/html/md/xml/json/yaml/sh/sql/properties/txt/cpp/h/py/c/.kt/mjs 共 20+ 种后缀，含 4 个最小化结构探针与 3 个命名/编辑探针。


## [v2] 工具更新后的回归验证（37 文件 / 113 锚点）
- 触发：被测锚点工具已按 v1 结论修复部分不一致问题，本轮回跑既有基线，并针对新规则补充语料与用例。
- 校验器升级：`harness/anchor_oracle.py` 的参照实现补上「排除目录段（24 项，精确段匹配）+ 点开头文件」，新增两份索引文件集一致性检查，并把 D1 白名单改为「必须不再出现」的回归哨兵。
- 本轮结论：**D1、D3 确认已修**，**D5 部分修复**，**D2 根因定位**，**D7 复现未修**，**并发现 1 项新回归 B1**（目录形 describe 出不了概览）。
- 最终状态：`oracle files=37, item diffs=0, file-level problems=0, excluded files=7` → `RESULT=PASS`（报告 `lab-out/oracle-report.txt`）。

### 修复验证
| 编号 | v1 现象 | v2 实测 |
|------|---------|---------|
| D1 | `_end` 后缀锚点缺失于 `.project_index.json` | ✅ 已修：两份索引文件集完全一致，`edit_target_scratch_end`、`end_rule_a_probe_end` 在项目索引中可见 |
| D3 | 索引未套用排除目录，与全文搜索口径不一致 | ✅ 已修：`build_anchor_index` 复用 `SearchFileFilter.DEFAULT_EXCLUDED_DIRS` 并跳过点开头文件；`probe/{dist,target,node_modules,__pycache__}`、`samples/pkg_inner/dist` 全部不入索引（本轮 hard-exclude 7 个文件）；全文搜索同步排除（只在 `probe/target/t.java` 出现的关键词搜索 0 命中） |
| D5 | describe 无法区分「文件不存在」与「文件无锚点」 | ⚠ 部分修复：文件形提示词已区分（文件存在但无锚点 → 「文件存在，但未标注任何锚点」）；目录形提示词仍与不存在路径同文案 |

### 本轮新增语料
- `samples/pkg_inner/dist/inside.js`（父目录段 = dist，应排除）、`samples/dist_named.js`（段名 dist_named.js ≠ dist，应收录）、`samples/build_here/keep.js`（build_here ≠ build，应收录）：验证排除规则是「路径段精确匹配」而非前缀/子串匹配。
- `probe/edit_roundtrip.js`：相邻端点的区间往返（insert → read → delete）。
- `probe/security/anchor_regex_probe.py`：安全扫描误报复现（D7）；顺带复现字符串内假锚点 `demo_token`（D8）。
- `harness/js_strip_probe.py`：JS 解析器根因探针（复刻取字步长）。

### 回归矩阵（增量用例，编号接 v1）
| # | 用例 | 预期 | 实测 |
|---|------|------|------|
| 27 | 排除目录「段精确匹配」（dist 目录 / dist_named.js / build_here 目录） | 仅段名等价者排除 | ✅ 三个探针与预期完全一致 |
| 28 | 目录形 describe（`samples`、`samples/nested`） | 输出 `_intro` 概览计数 | ❌ 返回「（目录存在，但目录下没有锚点记录）」→ **B1 回归** |
| 29 | describe 命中排除目录下的文件（`probe/dist/d.js`） | 按「不在索引」处理 | ✅ 提示「文件存在，但未标注任何锚点」 |
| 30 | describe 不存在路径（`ghost/none.js`） | 提示无锚点 | ✅ 与 v1 同文案 |
| 31 | `_end` 锚点参与 read / insert / delete | 与普通锚点等价 | ✅ 区间读取、定位、索引展示均正常 |
| 32 | 区间删除是否保留起始锚点的描述行 | 只删两端之间 | ✅ 会连带删除起始锚点描述行（本次删 3 行 = 描述 + 空行 + 插入内容），与实现一致，已在探针注释中提示 |
| 33 | 相邻端点区间删除 | 提示无内容可删 | ✅ 「两个锚点之间没有内容可删除」 |
| 34 | 非法 position / 未知 id / 重名无 file（写路径） | 分类报错 | ✅ 三种错误文案均按预期返回，且未污染文件 |
| 35 | 编辑后索引自动刷新（不手动重建） | 新锚点立即可见 | ✅ 新增 `oracle_exclusions` 锚点未经 `build_anchor_index` 即出现在 `.project_index.json` |
| 36 | get_file_structure：`.js` / `.ts` | 输出结构与锚点 | ❌ 仍仅回显「语言: JavaScript」（D2 未修） |
| 37 | 含「锚点标记 + 反斜杠」的正则源码扫描 | 不应报路径穿越 | ❌ 报 `FILE_PATH_TRAVERSAL: r:\`（D7 未修） |

### 差异与问题清单（更新）
- **B1（本轮新增回归）**：`AnchorFormatter.appendDescribeOne` 先做「文件名后缀匹配」再做「磁盘存在性判断」，目录形提示词命中 `Files.isDirectory` 即提前 return，永远走不到目录概览：`describe_anchors(file='samples')` 与 `file='.'` 行为不一致。规避：概览统一用 `file='.'`，或改传具体文件路径。
- **D2 根因（本轮定位）**：`JavaScriptParser.stripStringsOnly` 的普通字符分支同时存在「for 自增」与「体内 i++」，实际步长为 2：`// @…` 行丢字符、`class C {` → `casC{`，锚点/类/方法正则全部失配，因此 JS/TS 结构解析恒为空、JS 锚点 symbol 恒为 None。旁证：`harness/js_strip_probe.py` 输出 `PARSER_INPUT_CORRUPTED=True`（7 行语料中 6 行被改动）。
- **D4 / D6 / D8**：状态同 v1，本轮未复测（D4 仍无法构造点目录语料；D8 属既有假阳性行为，本轮再次观测到字符串内假锚点）。
- **文档级不一致**：`AnchorIndex.buildIndexEntries` 注释写「跳过 _end 锚点」，实现并未跳过——系 D1 修复后的陈述残留，易误导后续维护。

### 复现方式
1. `build_anchor_index { project_path: "tools-lab" }` → 37 文件 / 113 锚点。
2. `compile_and_run { filename: "tools-lab/harness/anchor_oracle.py", mode: "python" }` → `RESULT=PASS`，报告落盘 `lab-out/oracle-report.txt`。
3. `compile_and_run { filename: "tools-lab/harness/js_strip_probe.py", mode: "python" }` → `PARSER_INPUT_CORRUPTED=True`（D2 根因）。
4. `compile_and_run { filename: "tools-lab/probe/security/anchor_regex_probe.py", mode: "python" }` → 被安全扫描拦截（D7 复现）。
5. 目录概览回归：`describe_anchors { project_path: "tools-lab", file: "samples" }` → 当前返回「（目录存在，但目录下没有锚点记录）」（B1）。



## [v3] 二次修复后的全量回归（40 文件 / 123 锚点）
- 触发：锚点工具再次更新（针对 v2 的 B1 / D2 等结论）。本轮先在 `workflow-read-only` 建索引精读源码规格，再回跑全部基线 + 新增用例。
- 源码规格比对（只读，未修改）：`AnchorFormatter.appendDescribeOne` 改为「命中索引文件名才走文件详情，否则一律交目录概览 + 文件系统诊断」（对应 B1）；`JavaScriptParser.stripStringsOnly` 由 for + 体内自增改为 while + 步长 1（对应 D2）；`ToolExecutor.getFileStructure` 的转发范围由 `.md` 扩到 `.md/.markdown/.txt`；`write_file` 点路径拒绝文案细化。
- 最终状态：`oracle files=40, item diffs=0, file-level problems=0, excluded files=7` → `RESULT=PASS`；`js_strip_probe` → `D2_FIXED=True`。

### 修复验证（v2 遗留项收口）
| 编号 | v2 现象 | v3 实测 |
|------|---------|---------|
| D2 | JS/TS 结构解析恒为空（取字步长 2） | ✅ 已修：`get_file_structure` 对 `.js/.ts/.mjs` 输出类/方法/顶层函数；`app.js` 锚点 symbol 7/9、`app.ts` 4/4；oracle 的 D2 哨兵 7/7 通过 |
| B1 | 目录形 describe 出不了概览 | ✅ 已修：`file='samples'` 返回「22/26 已标注 _intro」；`samples/nested`、`probe` 同样正常 |
| D5 | 文件形已区分、目录形未区分 | ✅ 已修：目录存在无锚点 → 「目录存在，但目录下没有锚点记录」（`probe/dist`、`samples/pkg_inner/dist`） |
| D7 | 锚点正则字面量被判为盘符路径 | ✅ 已修：`probe/security/traversal_recheck.py`（含标记 + 反斜杠转义）写入成功并被索引收录 |
| D4 | 点路径不可写 | ⚠ 仍未修复（文案更明确，引导改用 describe_anchors / get_file_structure）：`.hidden/probe.js` 被拒绝 |
| D1 / D3 | `_end` 缺于项目索引 / 索引未套排除目录 | ✅ 保持修复：两份索引文件集一致；hard-exclude 7 个探针文件 |

### 本轮新增语料/探针与工具升级
- `probe/v3_edit_probe.js`（insert/read/delete 往返，附复原后的基准内容与实测要点注释）、`probe/adjacent_probe.js`（严格相邻端点）、`probe/security/traversal_recheck.py`（D7 复测语料）。
- `harness/anchor_oracle.py`：新增 D2 SENTINEL（7 个哨兵 JS/TS 文件必须携带 symbol）+ `spec version = v3` 行；重写 `main` 以挂载哨兵。
- `harness/js_strip_probe.py`：重写为「旧步长 2 / 新步长 1」双向复刻 + 从 `.project_index.json` 读取 JS/TS symbol 的端到端证据。

### 回归矩阵（增量用例，编号接 v2）
| # | 用例 | 预期 | 实测 |
|---|------|------|------|
| 38 | 目录形 describe（`samples` / `samples/nested` / `probe`） | 输出 _intro 概览计数 | ✅ 概览正常（B1 修复确认） |
| 39 | 目录形提示词带尾斜杠（`samples/`） | 同 `samples` | ❌ 落到「目录存在，但目录下没有锚点记录」（B2 观察） |
| 40 | `get_file_structure`：`.js` / `.ts` / `.mjs` | 输出结构与锚点 | ✅ 类/方法/顶层函数/锚点齐备（D2 修复确认） |
| 41 | `get_file_structure`：`.txt` / `.md` | 转发锚点描述 | ✅ 均返回锚点清单 |
| 42 | `get_file_structure`：未知扩展名（`.c` / `.kt`）与不存在文件 | 兜底「语言: text」+ 锚点；缺失分类报错 | ✅ 均符合预期 |
| 43 | 结构视图锚点清单 vs 索引 | 期望一致 | ⚠ 结构视图不含字符串内假锚点，且不做同文件重名 `_2` 去重（口径差异） |
| 44 | insert(after) / insert(before) 位置语义 | 正确插入且锚点保留 | ✅ after 会挤压锚点描述行；before 不影响描述归属 |
| 45 | delete 区间含描述行/空行 | 只保留两端锚点行 | ✅ 连删 2~5 行，两端锚点行保留，index 即时刷新 |
| 46 | 相邻端点区间删除 | 告警无内容可删 | ✅ 「两个锚点之间没有内容可删除」 |
| 47 | 编辑后索引刷新时机 | 行号即时、desc 本轮末 | ✅ 同一轮内新建文件 describe 不可见，下一轮可见 |
| 48 | 非法 position / 未知 id | 分类报错且不写文件 | ✅ 「position 必须是 'before' 或 'after'」/「未找到唯一锚点」 |
| 49 | 跨文件同名锚点（未给 file） | 报歧义并列候选 | ✅ 列出 `dup/Same.java`、`dup2/Same.java` |
| 50 | describe 缺 file 参数 / 项目不存在 | 分类报错 | ✅ 「必须指定 file 参数」/「项目目录不存在」 |
| 51 | 排除目录语义（dist 目录 / dist_named.js / build_here） | 仅段名等价者排除 | ✅ 与预期一致（excluded files=7） |
| 52 | 复原流程（write_file 写回基准内容） | 索引与行号重新对齐 | ✅ 复原后 describe 回到 3 个锚点、行号重算 |

### 结论
- v2 遗留的 D2、B1 已修复，D5、D7 收口；D1、D3 保持修复；D4、D6 状态不变。锚点扫描/描述/去重/编辑全部与参照规格一致（item diffs=0）。
- 新增 4 条观察（B2 尾斜杠、目录匹配偏宽松、索引刷新时机、结构视图锚点口径差异）与 1 条跨文件同名锚点歧义行为，均非缺陷但易误用，已写入 PROJECT.md 台账。

### 复现方式
1. `build_anchor_index { project_path: "tools-lab" }` → 40 文件 / 123 锚点。
2. `compile_and_run { filename: "tools-lab/harness/anchor_oracle.py", mode: "python" }` → `RESULT=PASS`，报告落盘 `lab-out/oracle-report.txt`。
3. `compile_and_run { filename: "tools-lab/harness/js_strip_probe.py", mode: "python" }` → `D2_FIXED=True`（旧算法 `ANCHOR_LINES_LOST_BY_OLD=10`）。


## [v4] 遗留项复核 + read_file / write_file 测试（43 文件 / 142 锚点）

### 本轮目标
- 复核 v3 遗留问题：D4 / D6 / D8 / B2 / 目录形匹配 / 索引刷新时机 / 跨文件歧义 / 结构视图口径。
- 把 `read_file` / `write_file` 纳入验证（旧只读源码仅作规格抽取，未修改；先对 `workflow-read-only` 建索引便于精读）。

### 本轮新增语料与工具
- `samples/long-text.log`：约 8.2 万字符（UTF-16）、1376 行、CRLF、无锚点无结构 —— 截断用例。
- `probe/io/`：`trunc_probe.txt`（13775 字符带行号）、`empty.txt`、`nonl.txt`、`crlf.txt`、`unicode.txt`、`deep/a/b/c/d.txt`、`nested_new/a.txt`、`bsep/name.txt`、`noext`、`with space.txt`、`dir_target`（尾斜杠产物）、`overwrite.txt`、`UPDATE.md`、`refresh_probe.js`。
- `probe/dist/inside_write.js`：写入排除目录的探针。
- `harness/io_oracle.py`：规格抽取（正则读源码）+ 16 条实测基线 + 12 条自动校验，Tee 落盘 `lab-out/io-report.txt`。
- `tmp/`：`inspect_io.py` / `analyze_log.py` / `boundary.py` / `boundary2.py` / `dump_index.py` / `verify_io.py`（一次性分析脚本，已去锚点化）。

### 用例矩阵与实测（编号接 v3）
| # | 用例 | 预期 | 实测 |
| --- | --- | --- | --- |
| 53 | read_file(notes.txt 小文件) | 头部 + 原文 | 一致 |
| 54 | read_file(trunc_probe.txt 13775 字符) | 完整返回 | 完整 300 行，无提示 → io-01 |
| 55 | read_file(long-text.log) | 截断并提示 | java≈50000 处截断 + 标准提示 |
| 56 | read_file(缺失路径) | 文件不存在… | 一致 |
| 57 | read_file(目录 / 目录带尾斜杠) | 文件不存在或是一个目录 | 三者同文案 |
| 58 | read_file(0 字节文件) | 仅头部 | 一致 |
| 59 | read_file(点开头路径) | 拒绝 | ❌ 不允许访问以 . 开头（D4） |
| 60 | read_file(名为 UPDATE.md) | 拒绝 | ❌ 提示改用 read_between_anchors |
| 61 | read_file(反斜杠路径) | 正常 | 一致 |
| 62 | read_file(unicode.txt) | 原样 | 中文/emoji/tab 原样 |
| 63 | write_file(新建 + 多级目录) | ✅ 并建目录 | ✅（nested_new/a.txt、deep/a/b/c/d.txt） |
| 64 | write_file(覆盖已有文件) | 整文件替换 | VERSION-1 → VERSION-2 |
| 65 | write_file(空内容) | 0 字节 | 0 字节 |
| 66 | write_file(无结尾换行) | 不补换行 | bytes=14，无 LF |
| 67 | write_file(含 CRLF) | 不归一化 | crlf=2 / lf=3 |
| 68 | write_file(名字含空格) | ✅ | 一致 |
| 69 | write_file(名字含反斜杠) | 当分隔符 | 生成 bsep/name.txt |
| 70 | write_file(无扩展名) | ✅ | 一致 |
| 71 | write_file(尾斜杠 + 不存在) | Path 归一化 | 落成普通文件 dir_target |
| 72 | write_file(目标是已存在目录) | 失败 | 写入文件失败: `<abs>/samples` |
| 73 | write_file(父路径是文件) | 失败 | 写入文件失败: `<abs>/probe/io/noext` |
| 74 | write_file(点开头路径) | 拒绝 | ❌ 同 D4 文案 |
| 75 | write_file(排除目录 dist/) | 成功但索引排除 | 先被即时刷收录，rebuild 后清理 → io-02 |
| 76 | write→同轮 describe(新文件) | 不可见 | 「文件存在，但未标注任何锚点」 |
| 77 | 下一轮 describe(同文件) | 可见 + symbol | L1 / refresh_probe_intro / refreshProbe |
| 78 | describe(file='samples/') | 目录概览 | 「目录存在，但目录下没有锚点记录」（B2） |
| 79 | describe(file='probe') | 目录概览 | 12 条，含 samples/probe/* 5 条（匹配偏宽松） |
| 80 | describe(file='Same.java') | 歧义报错 | 列出 dup/Same.java、dup2/Same.java |
| 81 | delete_file(io/UPDATE.md) | 拒绝 | ❌ UPDATE.md 不允许删除 |
| 82 | 同轮索引巡检 | 两份不同步 | A=48 / P=47，only_A=本轮新写文件（即时刷 vs 轮末 flush） |
| 83 | build_anchor_index 后巡检 | 一致 + 清理 dist | 43/43 一致，dist 条目消失 |
| 84 | harness/io_oracle.py | RESULT=PASS | 12 校验 PASS（C2 记 io-01）、16 基线 3 KNOWN |
| 85 | harness/anchor_oracle.py 回跑 | RESULT=PASS | item diffs=0、file-level problems=0 |

### 复核结论（v3 遗留项）
- **D4 仍存在**：点开头路径被 `checkPath` 一律拒绝（读/写/删同一文案），「点目录是否被索引排除」依旧无法构造；读索引改走 Python 侧。
- **D6 仍存在**：`compile_and_run(mode=java)` 子目录主类名推导问题未变（本 lab 只用 Python 模式）。
- **D8 仍存在**：`samples/md_anchor_example.md` 的 4 个 `mirror_*` 假锚点仍被两份索引收录（desc 为空）。
- **B2 仍存在**：describe 目录形带尾斜杠不归一（落到「目录存在但无锚点」）；write_file 尾斜杠则被 Path 归一化。
- **目录形匹配偏宽松、刷新时机、跨文件歧义、结构视图口径**四项复核结果与 v3 记载一致。
- 已修项 D1 / D2 / D3 / D5 / D7 本轮仍为修复态（两 oracle 哨兵均 PASS）。

### 新增差异（IO）
- **io-01**：`read_file` schema 描述「限制 5000 字符」与实现 `MAX_LENGTH=50000` 不符（描述陈旧）。证据：13775 字符文件完整返回；截断点为 java≈50000。
- **io-02**：`write_file` 的即时刷新不套用排除目录过滤，写入 `probe/dist/` 的文件会进两份索引，直到 `build_anchor_index` 重建才清理。

### 复现方式
1. `build_anchor_index`（project_path=`tools-lab`）。
2. `compile_and_run`（mode=`python`）→ `harness/anchor_oracle.py`，控制台 `RESULT=PASS`，写 `lab-out/oracle-report.txt`。
3. `compile_and_run`（mode=`python`）→ `harness/io_oracle.py`，控制台 `RESULT=PASS`，写 `lab-out/io-report.txt`。
4. 抽取规格：`read_between_anchors` 读 `workflow-read-only/.../FileOperator.java` 的 `fileOperator_readFile`、`ToolExecutor.java` 的 `toolExecutor_checkPath`、`ToolDefinitions.java` 的 `toolDef_readFile`。


### v4 补充复核（D6 与结构视图，同日追加）
| # | 用例 | 预期 | 实测 |
| --- | --- | --- | --- |
| 86 | compile_and_run(mode=java) 项目根 `HelloRoot.java` | 可运行 | ✅ 运行成功 |
| 87 | compile_and_run(mode=java) 子目录 `probe/java_sub/Hello.java` | v3 记「子目录必 CNFE」 | ✅ 运行成功 → D6 未复现 |
| 88 | compile_and_run(mode=java) 子目录 + `package probe.java_sub.pkg` 的 `P.java` | 包名导致主类名推导失败？ | ✅ 运行成功 |
| 89 | compile_and_run(mode=java) `probe/java_sub/Sub.java`（内含非 public 类 `Other`） | 主类名按文件名推导 | ❌ `ClassNotFoundException: Sub` → D6 收敛为「不解析源码取主类名」 |
| 90 | compile_and_run(mode=java) `probe/src/s.java`（`public class S` 与文件名不符） | 编译期即报错 | ❌ javac：应声明于 S.java |
| 91 | get_file_structure(samples/app.js) | 与索引口径不同 | 列 8 条：字符串假锚点缺席、重名不做 `_2` 去重（两处 `app_js_dup`） |

- **D6 结论改记**：原「子目录 java 模式必失败」在三种形态下均未复现；真实限制是主类名按文件 basename 推导，文件名与主类名不一致（非 public 类）才 CNFE。探针保留 `probe/java_sub/{Hello,Sub}.java`（均带 `预期:` 注释）。
- 清理：删除临时对照文件 `HelloRoot.java`、`probe/java_sub/pkg/P.java`；`probe/io/UPDATE.md` 保留（read_file/delete_file 拒绝规则用例）。


### v4 收尾（回归冻结）
- 冻结基线：**44 文件 / 134 锚点**，`harness/anchor_oracle.py` 与 `harness/io_oracle.py` 均 `RESULT=PASS`（item diffs=0、file-level problems=0、io 自动校验 12 条无意外失败）。
- 观察：`compile_and_run(mode=java)` 会在源文件同级建 `classes/` 放字节码（`classes` 属排除段，不影响索引），删除源文件不会自动清理其 `.class`（本轮已手工 `delete_file` 清理）。
- 差异台账最终状态：已修 D1/D2/D3/D5/D7；未修 D4；D6 改记为「主类名按文件名推导」；D8 既有行为；新增 io-01 / io-02。


<!-- @anchor: update_record_anchor -->
<!-- 追加区：新记录插入本锚点之前 -->

<!-- @anchor: update_record_000 -->
## [初始] lab 骨架与语料建立
- 目的：为锚点操作工具建立黑盒测试基线。
- 内容：PROJECT.md 定位/结构/规范；TODO.md 步骤清单；samples/ 多语言语料。
- 预期：语料可被 `build_anchor_index` 收录，`describe_anchors` 能列出锚点/描述/符号。
- 结果：见后续条目。
