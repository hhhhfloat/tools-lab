# @anchor-id: verify_io_intro
# 落盘巡检：确认 write_file 的产物形态（目录结构 / 换行 / 编码 / 反斜杠与尾斜杠行为）。
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = os.path.join(BASE, "probe", "io")

print("-- walk probe/io --")
for dirpath, dirnames, filenames in os.walk(root):
    rel = os.path.relpath(dirpath, BASE).replace("\\", "/")
    print("  DIR  %s  (dirs=%s)" % (rel, sorted(dirnames)))
    for f in sorted(filenames):
        p = os.path.join(dirpath, f)
        raw = open(p, "rb").read()
        print("    %-24s bytes=%-6d crlf=%-4d lf=%-4d first=%r"
              % (f, len(raw), raw.count(b"\r\n"), raw.count(b"\n"), raw[:40]))

print("\n-- dir_target 形态 --")
p = os.path.join(root, "dir_target")
print("  exists=%s isdir=%s isfile=%s" % (os.path.exists(p), os.path.isdir(p), os.path.isfile(p)))
if os.path.isdir(p):
    print("  entries=%s" % sorted(os.listdir(p)))

print("\n-- bsep 反斜杠处理 --")
print("  bsep dir: %s" % sorted(os.listdir(os.path.join(root, "bsep")))
      if os.path.isdir(os.path.join(root, "bsep")) else "  no bsep dir")

print("\n-- 索引中的 probe/io 条目 --")
a = json.loads(open(os.path.join(BASE, ".anchors.json"), encoding="utf-8").read())
print("  %s" % [k for k in a if k.startswith("probe/io")])
