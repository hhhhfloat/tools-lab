// search 语料 + 删除/索引刷新探针（token: stale_probe_7q）
// @anchor: search_idx_stale_probe
// 删除后索引刷新时机探针：带一个锚点，用于观察 delete_file 是否触发索引清理
// 预期: delete_file 不调用 markDirtyByFilename，故两份索引会残留本文件条目直到 rebuild（del-01）
const STALE = 1;
