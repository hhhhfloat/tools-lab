# @anchor-id: dump_index_intro
# 索引巡检：列出两份索引的文件集差、条目差，以及关键探针的收录情况。
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    return json.loads(open(os.path.join(BASE, name), encoding="utf-8").read())


a = load(".anchors.json")
d = load(".project_index.json")
na = sum(len(v) for v in a.values())
nd = sum(len(v) for v in d.values())
print("anchors.json     files=%d items=%d" % (len(a), na))
print("project_index    files=%d items=%d" % (len(d), nd))
print("only_in_anchors : %s" % sorted(set(a) - set(d)))
print("only_in_project : %s" % sorted(set(d) - set(a)))

for k in sorted(set(a) & set(d)):
    ia = [x["id"] for x in a[k]]
    idp = [x["id"] for x in d[k]]
    if ia != idp:
        print("ITEM_DIFF %s\n   A=%s\n   P=%s" % (k, ia, idp))

print("\n-- 排除目录相关 --")
print("   probe/dist/inside_write.js in A: %s / in P: %s"
      % ("probe/dist/inside_write.js" in a, "probe/dist/inside_write.js" in d))

print("\n-- tmp/*.py 是否污染索引 --")
print("   tmp entries: %s" % [k for k in a if k.startswith("tmp/")])

print("\n-- D8 假锚点 --")
print("   md_anchor_example.md ids: %s" % [x["id"] for x in a.get("samples/md_anchor_example.md", [])])
