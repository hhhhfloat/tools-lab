# anchor-id: analyze_log_intro
# 分析 long-text.log：定位「文件过长」提示、各次迭代的字符偏移，用于推算 read_file 的截断点。
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(BASE, "samples", "long-text.log")
text = open(p, "r", encoding="utf-8", errors="replace").read()
print("total_chars=%d" % len(text))

note = "文件过长"
idx = 0
while True:
    i = text.find(note, idx)
    if i < 0:
        break
    print("  NOTE at char %d : %s" % (i, text[i - 20:i + 30].replace("\n", "\\n")))
    idx = i + 1

for tag in ["第 21 次迭代", "第 22 次迭代", "第 25 次迭代", "第 30 次迭代"]:
    i = text.find(tag)
    print("  %-12s -> char %d" % (tag, i))

print("first 80: %r" % text[:80])
