# @anchor: anchor_oracle_intro
# 独立差分校验器：按 workflow-read-only 的扫描规格重写参照实现，与真实工具产出的索引逐条比对
# 输出统一使用 ASCII，避免 Windows 控制台编码导致中文乱码
import json
import re
import sys
from pathlib import Path

# @anchor: oracle_spec
# 与 AnchorScanner 保持一致的规格：扩展名白名单 + 4 种注释风格的单行锚点正则
AT = "@anchor" + ":"
W = r"(\w+)"
TEXT_EXTENSIONS = [
    ".java", ".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx",
    ".txt", ".xml", ".json", ".md", ".properties", ".yml", ".yaml",
    ".sh", ".bat", ".gradle", ".sql",
    ".cpp", ".cc", ".cxx", ".h", ".hpp", ".py", ".pyw",
]

ANCHOR_PATTERN = re.compile(
    r"//\s*" + AT + r"\s*" + W + "|"
    r"/\*\s*" + AT + r"\s*" + W + r"\s*\*/|"
    r"<!--\s*" + AT + r"\s*" + W + r"\s*-->|"
    r"#\s*" + AT + r"\s*" + W
)

# @anchor: oracle_exclusions
# 与 SearchFileFilter.DEFAULT_EXCLUDED_DIRS 逐字对齐的排除目录段名（任一段命中即排除）
EXCLUDED_DIRS = [
    "target", "build", "out", "dist", "bin", "obj", "classes",
    "node_modules", ".gradle", ".mvn", ".cache", "vendor",
    ".git", ".svn", ".hg", ".idea", ".vscode", ".settings",
    "__pycache__", ".pytest_cache", "venv", ".venv",
    "coverage", ".nyc_output",
]


# 参照实现：相对路径任一段命中排除集即视为不参与索引
def is_excluded_rel(rel):
    return any(seg in EXCLUDED_DIRS for seg in rel.split("/"))


# @anchor: oracle_extract_desc
# 参照实现：从锚点下一行紧邻注释提取描述（与工具逻辑同构）
def extract_desc(lines, idx):
    nxt = idx + 1
    if nxt >= len(lines):
        return ""
    line = lines[nxt].strip()
    if not line:
        return ""
    if ANCHOR_PATTERN.search(line):
        return ""
    if line.startswith("//"):
        c = line[2:].strip()
        return "" if ANCHOR_PATTERN.search(c) else c
    if line.startswith("#") and not line.startswith("#!"):
        c = line[1:].strip()
        return "" if ANCHOR_PATTERN.search(c) else c
    if line.startswith("/**") or line.startswith("/*"):
        rest = line[3:].strip() if line.startswith("/**") else line[2:].strip()
        if rest.endswith("*/"):
            rest = rest[:-2].strip()
        if rest:
            return rest
        for l in lines[nxt + 1:]:
            l = l.strip()
            if l == "*/":
                return ""
            if ANCHOR_PATTERN.search(l):
                return ""
            if l.startswith("*"):
                l = l[1:].strip()
            if l.endswith("*/"):
                l = l[:-2].strip()
            if l:
                return l
        return ""
    if line.startswith("<!--"):
        rest = line[4:].strip()
        if rest.endswith("-->"):
            rest = rest[:-3].strip()
        return rest
    return ""

# @anchor: oracle_scan
# 参照实现：扫描单个文件，产出 id/line/desc（文件内重名自动加 _2 后缀）
def scan(path):
    out = []
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return out
    lines = path.read_text(encoding="utf-8").splitlines()
    seen = set()
    for i, line in enumerate(lines):
        m = ANCHOR_PATTERN.search(line)
        if not m:
            continue
        aid = None
        for g in m.groups():
            if g is not None:
                aid = g
                break
        if aid is None:
            continue
        final_id = aid
        suffix = 2
        while final_id in seen:
            final_id = "%s_%d" % (aid, suffix)
            suffix += 1
        seen.add(final_id)
        out.append({"id": final_id, "line": i + 1, "desc": extract_desc(lines, i)})
    return out

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# @anchor: oracle_report_sink
# 报告留证：把控制台输出同时写入 lab-out/oracle-report.txt（Tee 模式）
class _Tee:
    def __init__(self, fp):
        self.fp = fp

    def write(self, text):
        self.fp.write(text)
        sys.__stdout__.write(text)

    def flush(self):
        self.fp.flush()
        sys.__stdout__.flush()


try:
    sys.__stdout__.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    _lab = Path(__file__).resolve().parents[1]
    (_lab / "lab-out").mkdir(exist_ok=True)
    sys.stdout = _Tee(open(_lab / "lab-out" / "oracle-report.txt", "w", encoding="utf-8"))
except Exception:
    pass


# @anchor: oracle_load_index
# 读取工具产出的 .anchors.json / .project_index.json
def load_index(path):
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as ex:
        print("  [WARN] index parse failed %s: %s" % (path.name, ex))
        return {}

# @anchor: oracle_known_diffs
# D1 回归哨兵：_end 锚点本应同时出现在两份索引中；若只在 .anchors.json 出现即判回归
def is_known_project_index_gap(anchor):
    return str(anchor.get("id", "")).endswith("_end")


# @anchor: oracle_d2_sentinel
# D2 回归哨兵：JS/TS 结构解析修复后，下列文件的锚点必须至少有一个归属到方法/函数符号
D2_EXPECT_SYMBOL_FILES = [
    "samples/app.js",
    "samples/app.ts",
    "samples/probe/min_class.js",
    "samples/probe/min_function.js",
    "samples/end_rule_a.js",
    "samples/dist_named.js",
    "samples/build_here/keep.js",
]


# 判定：哨兵文件若失去全部 symbol，即认为 JS 结构解析退回「恒为空」
def check_d2(desc_index):
    found = []
    print("== D2 SENTINEL (js/ts structure symbols) ==")
    for rel in sorted(desc_index):
        if not rel.lower().endswith((".js", ".jsx", ".ts", ".tsx")):
            continue
        items = desc_index[rel] or []
        syms = [d.get("symbol") for d in items if d.get("symbol")]
        print("  %s symbols=%d/%d %s" % (rel, len(syms), len(items), syms))
    missing = [rel for rel in D2_EXPECT_SYMBOL_FILES
               if not any(d.get("symbol") for d in (desc_index.get(rel) or []))]
    if missing:
        print("  [REGRESSION-D2] files without any symbol: %s" % missing)
        found.append("d2:" + ",".join(missing))
    else:
        print("  all %d sentinel js/ts files carry symbols -> D2 (empty JS structure) NOT reproduced"
              % len(D2_EXPECT_SYMBOL_FILES))
    print()
    return found



# @anchor: oracle_main
# 入口：按规格（白名单 + 排除目录 + 点文件 + 点路径）重算，再与两份真实索引逐条差分
def main():
    project = resolve_project()
    print("== ENV ==")
    print("cwd     = %s" % Path.cwd())
    print("project = %s" % project.resolve())
    print()
    print("== SPEC (mirrors AnchorScanner + AnchorIndex.rebuild) ==")
    print("text extensions      = %d" % len(TEXT_EXTENSIONS))
    print("exclude dir segments = %d" % len(EXCLUDED_DIRS))
    print("skip dot-named files = True")
    print("spec version         = v3 (js/ts structure sentinel + index-set sentinel)")
    print()

    anchors_index = load_index(project / ".anchors.json")
    desc_index = load_index(project / ".project_index.json")
    print("== INDEX SIZE == anchors.json files=%d, project_index.json files=%d"
          % (len(anchors_index), len(desc_index)))
    print("   note: .anchors.json carries id/line/preview only; desc lives in .project_index.json")
    problems = []
    set_diff = sorted(set(anchors_index) ^ set(desc_index))
    if set_diff:
        print("   [INDEX-SET-DIFF] %s" % set_diff)
        problems.append("index-set-diff")
    else:
        print("   two index file sets identical -> D1 (missing _end in project index) NOT reproduced")
    print()

    oracle = {}
    excluded = []
    print("== FILE LEVEL ==")
    for f in sorted(project.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(project).as_posix()
        if rel.startswith(".") or "/." in rel:
            continue
        if is_excluded_rel(rel):
            excluded.append(rel)
            continue
        mine = scan(f)
        in_index = rel in anchors_index
        if mine and not in_index:
            print("  [MISSING] %s oracle=%d index=none -> not covered by exclude rules" % (rel, len(mine)))
            problems.append("missing:" + rel)
        elif not mine and in_index:
            print("  [EXTRA-FILE] %s oracle=0 index=%d" % (rel, len(anchors_index[rel])))
            problems.append("extra-file:" + rel)
        elif mine:
            real = anchors_index[rel]
            status = "OK" if len(mine) == len(real) else "COUNT-DIFF"
            print("  [%s] %s oracle=%d index=%d" % (status, rel, len(mine), len(real)))
            if status != "OK":
                problems.append("count:" + rel)
            oracle[rel] = mine
    print("  excluded-by-dir (must be absent from index): %s" % excluded)
    print()

    print("== PER-ITEM DIFF (id/line/desc) ==")
    diff = 0
    for rel, mine in sorted(oracle.items()):
        real = anchors_index.get(rel, [])
        detail = desc_index.get(rel) or []
        for a in mine:
            match = next((r for r in real
                          if r.get("id") == a["id"] and str(r.get("line")) == str(a["line"])), None)
            if match is None:
                print("  [ONLY-ORACLE] %s id=%s L%s" % (rel, a["id"], a["line"]))
                diff += 1
                continue
            td = next((d.get("desc") or "" for d in detail if d.get("id") == a["id"]), None)
            if td is None:
                if is_known_project_index_gap(a):
                    print("  [REGRESSION-D1] %s id=%s absent from project_index.json" % (rel, a["id"]))
                    problems.append("d1:" + rel + ":" + a["id"])
                else:
                    print("  [MISSING-IN-PROJECT-INDEX] %s id=%s" % (rel, a["id"]))
                    diff += 1
                continue
            if a["desc"] != td:
                print('  [DESC-DIFF] %s id=%s oracle="%s" tool="%s"' % (rel, a["id"], a["desc"], td))
                diff += 1
        for r in real:
            if not any(a["id"] == r.get("id") and str(a["line"]) == str(r.get("line")) for a in mine):
                print("  [ONLY-INDEX] %s id=%s L%s" % (rel, r.get("id"), r.get("line")))
                diff += 1
    if diff == 0 and not problems:
        print("  no diff")
    print()

    print("== SYMBOL COLUMN (project_index.json) ==")
    for rel in sorted(desc_index):
        items = desc_index[rel] or []
        print("  %s: %s" % (rel, "  ".join("%s->%s" % (d.get("id"), d.get("symbol")) for d in items)))
    print()

    problems.extend(check_d2(desc_index))

    print("== SUMMARY ==")
    print("oracle files=%d, item diffs=%d, file-level problems=%d, excluded files=%d"
          % (len(oracle), diff, len(problems), len(excluded)))
    print("RESULT=%s" % ("PASS" if diff == 0 and not problems else "CHECK"))
    if problems:
        print("problems=%s" % problems)



# @anchor: oracle_resolve_project
# 定位 lab 根目录：默认取脚本上级目录，允许命令行参数覆盖
def resolve_project():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    return Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    main()
