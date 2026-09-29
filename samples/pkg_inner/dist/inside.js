// @anchor: pkg_inner_dist_js
// 排除目录语义探针：父目录段为 dist
// 预期: 段名精确命中排除集（dist）→ 不进入 .anchors.json / .project_index.json

function insideExcludedDir() {
  return 1;
}
