# @anchor: index_snapshot_intro
# 索引快照工具：定位项目根后打印两份索引的文件集合并对比（D1 哨兵），供 io-02 与 delete_file 用例取证。
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def find_base():
    here = Path(__file__).resolve()
    for c in [here.parents[1], Path.cwd()]:
        if (c / ".anchors.json").exists() or (c / "PROJECT.md").exists():
            return c
    return here.parents[1]


BASE = find_base()

WATCH = [
    "probe/dist/inside_write.js",
    "probe/dist/d.js",
    "probe/dist/io2_probe.js",
    "search/idx_stale.js",
    "search/dist/excluded.js",
    "search/delete_me.js",
]


def load(name):
    p = BASE / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main():
    print("[env] file=%s cwd=%s base=%s" % (Path(__file__).resolve(), Path.cwd(), BASE))
    a = load(".anchors.json")
    d = load(".project_index.json")
    print("[index snapshot] A=%d P=%d" % (len(a), len(d)))
    only_a = sorted(set(a) - set(d))
    only_p = sorted(set(d) - set(a))
    print("only_A=%s" % only_a)
    print("only_P=%s" % only_p)
    print("D1_CONSISTENT=%s" % (sorted(a) == sorted(d)))
    for k in WATCH:
        print("  has(%-30s): A=%s P=%s" % (k, k in a, k in d))
    dist = sorted(k for k in set(a) | set(d) if "/dist/" in k or "/target/" in k)
    print("dist/target entries=%s" % dist)


if __name__ == "__main__":
    main()
