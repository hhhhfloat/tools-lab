# @anchor: search_oracle_intro
# search_text 差分校验器：从只读源码抽规格 + 独立重实现搜索语义 → 与实测转录逐条差分 → 报告落盘 lab-out/search-report.txt。
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parents[1]     # tools-lab
SANDBOX = BASE.parent                           # sandbox
LABOUT = BASE / "lab-out"
WF = SANDBOX / "workflow-read-only"


class _Tee:
    def __init__(self, fp):
        self.fp = fp

    def write(self, text):
        sys.stdout.write(text)
        self.fp.write(text)

    def flush(self):
        sys.stdout.flush()
        self.fp.flush()


# @anchor: search_oracle_spec
# 规格抽取：TEXT_EXTENSIONS / MAX_RESULTS / 预览截断阈值 / 排除集 / 消息模板（纯文本匹配，不执行源码）
def _body(src, sig):
    i = src.find(sig)
    if i < 0:
        return ""
    j = src.find("{", i)
    if j < 0:
        return src[i:]
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
    return src[i:]


def extract_spec():
    ts = (WF / "src/main/java/com/myagent/workflow/tools/TextSearcher.java").read_text(encoding="utf-8")
    sf = (WF / "src/main/java/com/myagent/workflow/tools/SearchFileFilter.java").read_text(encoding="utf-8")
    td = (WF / "src/main/java/com/myagent/workflow/tools/ToolDefinitions.java").read_text(encoding="utf-8")
    spec = {}
    m = re.search(r"TEXT_EXTENSIONS = Arrays\.asList\((.*?)\);", ts, re.S)
    spec["extensions"] = re.findall(r'"([^"]+)"', m.group(1))
    spec["max_results"] = int(re.search(r"final int MAX_RESULTS = (\d+);", ts).group(1))
    spec["preview_limit"] = int(re.search(r"preview\.length\(\) > (\d+)\)", ts).group(1))
    dm = re.search(r"DEFAULT_EXCLUDED_DIRS = List\.of\((.*?)\);", sf, re.S)
    spec["excluded_dirs"] = re.findall(r'"([^"]+)"', dm.group(1))
    fm = re.search(r"DEFAULT_EXCLUDED_FILES = List\.of\((.*?)\);", sf, re.S)
    spec["excluded_files"] = re.findall(r'"([^"]+)"', fm.group(1))
    body = _body(ts, "String searchText(")
    spec["no_match_msg"] = "🔍 未找到匹配 " in body
    spec["found_msg"] = "🔍 找到 " in body
    spec["more_hint"] = "仅显示前 " in body
    spec["badregex_msg"] = "关键词正则表达式错误: " in body
    spec["badpath_msg"] = "路径不存在或不是目录: " in body
    spec["declared_max"] = int(re.search(r"结果限制最多 (\d+) 条", td).group(1))
    guard = body.find("if (resultCount.get() >= MAX_RESULTS) break;")
    incr = body.find("matchCount.incrementAndGet();")
    spec["cap_before_count"] = 0 <= guard < incr
    return spec


# @anchor: search_oracle_ref
# 参照实现：复刻 TextSearcher.searchText 的文件收集 / 扩展名过滤 / 正则 find / 预览 / 30 条上限
def parse_file_patterns(file_pattern):
    if not file_pattern or not file_pattern.strip() or file_pattern.strip() == ".*":
        return []
    out = []
    for p in file_pattern.split(","):
        p = p.strip()
        out.append(p[1:] if p.startswith("*.") else p)
    return out


def matches_extension(file_name, patterns, default_exts):
    ext = ""
    dot = file_name.rfind(".")
    if dot > 0:
        ext = file_name[dot:].lower()
    if patterns:
        for pat in patterns:
            if pat.startswith(".") and ext == pat:
                return True
            if ext == "." + pat:
                return True
            if file_name.endswith(pat):
                return True
        return False
    return ext in default_exts


def collect_files(start, excluded_dirs, excluded_files):
    files = []
    for root, dirs, names in os.walk(start):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for n in names:
            if n in excluded_files:
                continue
            files.append(Path(root) / n)
    return files


def ref_preview(line):
    p = line.strip()
    return p[:80] + "..." if len(p) > 80 else p


def ref_search(keyword, file_pattern, path, spec):
    start = SANDBOX / path
    if not start.is_dir():
        return "路径不存在或不是目录: " + path
    try:
        pattern = re.compile(keyword)
    except re.error as e:
        return "关键词正则表达式错误: %s。如需普通文本搜索，请转义特殊字符。" % e
    patterns = parse_file_patterns(file_pattern)
    hits = []
    for f in collect_files(start, spec["excluded_dirs"], spec["excluded_files"]):
        if len(hits) >= spec["max_results"]:
            break
        if not matches_extension(f.name, patterns, spec["extensions"]):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = os.path.relpath(f, start).replace("\\", "/")
        for i, line in enumerate(text.splitlines(), 1):
            if len(hits) >= spec["max_results"]:
                break
            if pattern.search(line):
                hits.append("%s:%d" % (rel, i))
    return hits


# @anchor: search_oracle_cases
# 实测转录：每条为一次真实 search_text 调用的「文件:行号」集合（相对 path 参数），由参照实现独立重算对比
CASES = [
    ("gammaFn", None, "tools-lab/search", "普通关键词 + 输出相对 path 的路径", [
        "app.js:1", "app.js:2", "app.js:4", "app.js:8",
        "lib/alpha.js:4", "lib/beta.js:4", "lib/gamma.js:2", "lib/gamma.js:3", "lib/gamma.js:7"]),
    ("EXCLUDEDNEEDLE", None, "tools-lab/search", "排除目录 dist 不参与搜索", []),
    ("LOGNEEDLE", None, "tools-lab/search", "默认扩展名白名单不含 .log", []),
    ("LOGNEEDLE", "*.log", "tools-lab/search", "显式 file_pattern 越过默认白名单", ["ext_samples/notes.log:1"]),
    ("parse\\(", None, "tools-lab/search", "转义后的正则元字符", ["regex_probe.txt:1", "regex_probe.txt:2"]),
    ("a.b", None, "tools-lab/search", "正则点号 = 任意字符", ["regex_probe.txt:3", "regex_probe.txt:4", "regex_probe.txt:5"]),
    ("pipe|alt", None, "tools-lab/search", "正则或分支", ["regex_probe.txt:8"]),
    ("manytoken", None, "tools-lab/search", "Pattern 默认区分大小写", []),
    ("NOEXTNEEDLE", None, "tools-lab/search", "无扩展名文件不在白名单", []),
    ("NOEXTNEEDLE", "plain", "tools-lab/search", "file_pattern 按 fileName.endsWith 匹配", ["ext_samples/plain:1"]),
    ("gammaFn", "*.js", "tools-lab/search/lib", "file_pattern=*.js + 限定子目录", [
        "alpha.js:4", "beta.js:4", "gamma.js:2", "gamma.js:3", "gamma.js:7"]),
    ("gammaFn", ".js", "tools-lab/search/lib", "file_pattern 直接给扩展名", [
        "alpha.js:4", "beta.js:4", "gamma.js:2", "gamma.js:3", "gamma.js:7"]),
    ("gammaFn", "js,py", "tools-lab/search", "file_pattern 逗号多值（无点也匹配）", [
        "app.js:1", "app.js:2", "app.js:4", "app.js:8",
        "lib/alpha.js:4", "lib/beta.js:4", "lib/gamma.js:2", "lib/gamma.js:3", "lib/gamma.js:7"]),
    ("gammaFn", "*.txt", "tools-lab/search", "模式不匹配则 0 命中", []),
    ("NEEDLE", None, "tools-lab/search", "子串命中（含后缀 token；dist 命中被排除）", ["long_line.txt:1"]),
    ("MANYTOKEN", None, "tools-lab/search", "命中 41 条 → 只显示前 30（sc-01：总数被截为 30）",
     ["many.txt:%d" % i for i in range(1, 31)]),
    # 关键词用相邻字符串隐式拼接，避免校验器自身源码命中该 token
    ("stale_probe_" "7q", ".*", "tools-lab", "排除文件（.anchors.json/.project_index.json）不参与搜索",
     ["search/idx_stale.js:1"]),
]

# 实测现象记录（非 PASS/FAIL，仅留证）
OBSERVATIONS = [
    ("obs-1", "命中 41 条的查询只报「🔍 找到 30 条匹配结果：」，无「仅显示前 30 条」提示（sc-01 死分支）"),
    ("obs-2", "keyword 按 Java 正则编译：a.b 命中 a+b/a.b/aXb；pipe|alt 生效；默认区分大小写（manytoken 0 命中）"),
    ("obs-3", "file_pattern 走 fileName.endsWith / 扩展名比对：'plain' / '.js' / 'js,py' 均可；'*' 之类不匹配则 0 命中"),
    ("obs-4", "非法正则 parse( → 「关键词正则表达式错误: Unclosed group near index 6」"),
    ("obs-5", "path 不存在 → 「路径不存在或不是目录: X」；path='.' 时输出带 'tools-lab/' 前缀"),
]



# @anchor: search_oracle_checks
# 规格与不变量校验：源码常量、消息模板、截断规则、sc-01 死分支
def run_checks(spec):
    results = []

    def check(cid, desc, ok, detail):
        results.append((cid, desc, ok, detail))

    check("S1", "MAX_RESULTS 抽取 == 30", spec["max_results"] == 30, "max_results=%d" % spec["max_results"])
    check("S2", "预览截断阈值 == 80", spec["preview_limit"] == 80, "preview_limit=%d" % spec["preview_limit"])
    check("S3", "工具声明上限 == 实现上限", spec["declared_max"] == spec["max_results"],
          "声明=%d 实现=%d" % (spec["declared_max"], spec["max_results"]))
    check("S4", "默认白名单含 .js/.txt/.py，不含 .log/.c/.mjs",
          all(e in spec["extensions"] for e in (".js", ".txt", ".py")) and
          not any(e in spec["extensions"] for e in (".log", ".c", ".mjs")),
          "extensions=%d 项" % len(spec["extensions"]))
    check("S5", "排除目录含 dist/target/node_modules",
          all(d in spec["excluded_dirs"] for d in ("dist", "target", "node_modules")),
          "excluded_dirs=%d 项" % len(spec["excluded_dirs"]))
    check("S6", "排除文件含 .anchors.json/.project_index.json",
          all(f in spec["excluded_files"] for f in (".anchors.json", ".project_index.json")),
          "excluded_files=%d 项" % len(spec["excluded_files"]))
    check("S7", "sc-01：计数发生在上限判断之后 → 「仅显示前 N 条」为死分支",
          spec["cap_before_count"] and spec["more_hint"],
          "guard_before_count=%s more_hint=%s" % (spec["cap_before_count"], spec["more_hint"]))
    line1 = (BASE / "search/long_line.txt").read_text(encoding="utf-8").splitlines()[0]
    prev = ref_preview(line1)
    check("S8", "preview = trim 后前 80 字符 + '...'（长度 83）",
          len(prev) == 83 and prev == "LONGNEEDLE " + "x" * 69 + "...",
          "len=%d" % len(prev))
    check("S9", "消息模板齐备（未找到 / 路径不存在 / 关键词正则错误）",
          spec["no_match_msg"] and spec["badpath_msg"] and spec["badregex_msg"],
          "no_match=%s badpath=%s badregex=%s" % (spec["no_match_msg"], spec["badpath_msg"], spec["badregex_msg"]))
    return results


# @anchor: search_oracle_main
# 入口：规格 → 转录差分 → 不变量校验 → 观测记录 → RESULT，并落盘报告
def main():
    LABOUT.mkdir(exist_ok=True)
    with open(LABOUT / "search-report.txt", "w", encoding="utf-8") as fp:
        out = _Tee(fp)
        spec = extract_spec()
        print("== search_text oracle ==", file=out)
        print("[spec] extensions=%d max_results=%d preview_limit=%d excluded_dirs=%d excluded_files=%d declared_max=%s"
              % (len(spec["extensions"]), spec["max_results"], spec["preview_limit"],
                 len(spec["excluded_dirs"]), len(spec["excluded_files"]), spec["declared_max"]), file=out)
        print("[extensions] %s" % " ".join(spec["extensions"]), file=out)

        print("\n[diff] 参照实现 vs 工具实测转录", file=out)
        fails = []
        for i, (kw, fpat, path, note, expected) in enumerate(CASES, 1):
            got = ref_search(kw, fpat, path, spec)
            ok = set(got) == set(expected)
            print("  D%02d %-6s %s\n        kw=%r pat=%r path=%s  ref=%d exp=%d"
                  % (i, "PASS" if ok else "FAIL", note, kw, fpat, path, len(got), len(expected)), file=out)
            if not ok:
                print("        only_ref=%s only_exp=%s"
                      % (sorted(set(got) - set(expected)), sorted(set(expected) - set(got))), file=out)
                fails.append(("D%02d" % i, note))

        print("\n[checks] 规格与不变量", file=out)
        for cid, desc, ok, detail in run_checks(spec):
            print("  %-4s %-6s %s | %s" % (cid, "PASS" if ok else "FAIL", desc, detail), file=out)
            if not ok:
                fails.append((cid, desc))

        print("\n[observations]", file=out)
        for oid, o in OBSERVATIONS:
            print("  %-6s %s" % (oid, o), file=out)

        print("\n[failures] %s" % (fails if fails else "none"), file=out)
        print("RESULT=%s" % ("PASS" if not fails else "CHECK"), file=out)


if __name__ == "__main__":
    main()
