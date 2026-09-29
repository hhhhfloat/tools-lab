// @anchor: build_here_keep_js
// 排除目录语义探针：目录名为 build_here（前缀相同但不等价）
// 预期: 段名不等价（build_here != build）→ 正常收录

function buildHereKept() {
  return 3;
}
