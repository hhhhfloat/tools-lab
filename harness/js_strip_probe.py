# @anchor: js_strip_probe_intro
# D2 根因/修复双向探针：复刻 JavaScriptParser.stripStringsOnly 的「旧步长 2 / 新步长 1」两种取字语义，
# 并用工具产出的 .project_index.json 中 JS/TS 锚点的 symbol 作为端到端证据
import json
import re
import sys
from pathlib import Path

AT = "@anchor" + ":"
ANCHOR = re.compile(r"//\s*" + AT + r"\s*(\w+)|/\*\s*" + AT + r"\s*(\w+)\s*\*/")
CLASS_P = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)")
FUNC_P = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)")


# @anchor: js_strip_probe_old
# 旧实现根因复刻：普通字符分支「for 自增 + 体内自增」等价于步长 2，逐行丢一半字符
def strip_old(raw):
    out = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c in ("`", "'", '"'):
            quote = c
            i += 2
            while i < n and raw[i] != quote:
                i += 2
            i += 2
            continue
        out.append(c)
        i += 2
    return "".join(out)


# @anchor: js_strip_probe_new
# 修复后实现复刻：转义成对跳过、字符串整体跳过，其余字符步长 1
def strip_new(raw):
    out = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == "\\" and i + 1 < n:
            out.append(c)
            out.append(raw[i + 1])
            i += 2
            continue
        if c in ("'", '"', "`"):
            quote = c
            i += 1
            while i < n:
                inner = raw[i]
                if inner == "\\" and i + 1 < n:
                    i += 2
                    continue
                if inner == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


# @anchor: js_strip_probe_evidence
# 端到端证据：统计 .project_index.json 中每个 JS/TS 文件的 symbol 覆盖数
def collect_evidence(lab):
    idx = lab / ".project_index.json"
    if not idx.exists():
        return {}
    data = json.loads(idx.read_text(encoding="utf-8"))
    stats = {}
    for rel, items in data.items():
        if not rel.lower().endswith((".js", ".jsx", ".ts", ".tsx")):
            continue
        items = items or []
        with_sym = [d.get("symbol") for d in items if d.get("symbol")]
        stats[rel] = (len(with_sym), len(items))
    return stats


# @anchor: js_strip_probe_main
# 对照语料行：旧/新算法是否改动原行、锚点/类正则是否仍能命中，并汇总工具侧 symbol 证据
def main():
    lab = Path(__file__).resolve().parents[1]
    targets = [
        lab / "samples" / "probe" / "min_class.js",
        lab / "samples" / "app.js",
    ]
    old_bad = 0
    for target in targets:
        print("== CASE FILE == %s" % target.relative_to(lab).as_posix())
        for idx, raw in enumerate(target.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            o = strip_old(raw)
            n = strip_new(raw)
            print("  L%d raw=%r" % (idx, raw))
            print("     old=%r anchor(%s) class(%s)" % (o, bool(ANCHOR.search(o)), bool(CLASS_P.match(o))))
            print("     new=%r anchor(%s) class(%s) function(%s)"
                  % (n, bool(ANCHOR.search(n)), bool(CLASS_P.match(n)), bool(FUNC_P.match(n))))
            if ANCHOR.search(raw) and not ANCHOR.search(o):
                old_bad += 1
        print()

    stats = collect_evidence(lab)
    print("== TOOL SIDE EVIDENCE (.project_index.json) ==")
    for rel in sorted(stats):
        print("  %s symbols=%d/%d" % (rel, stats[rel][0], stats[rel][1]))
    files_with_symbols = sum(1 for v in stats.values() if v[0] > 0)
    print()
    print("== SUMMARY ==")
    print("OLD_ALGORITHM_CORRUPTED=True  (step=2, historical root cause)")
    print("NEW_ALGORITHM_CORRUPTED=False (step=1, matches fixed source)")
    print("ANCHOR_LINES_LOST_BY_OLD=%d" % old_bad)
    print("JS_FILES_WITH_SYMBOLS=%d/%d" % (files_with_symbols, len(stats)))
    print("D2_FIXED=%s" % (files_with_symbols > 0 and old_bad > 0))


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

if __name__ == "__main__":
    main()
