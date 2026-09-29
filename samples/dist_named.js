// @anchor: dist_named_js
// 排除目录语义探针：文件名含 dist 但段名不等于 dist
// 预期: 段名不等价（dist_named.js != dist）→ 正常收录

function distNamedKept() {
  return 2;
}
