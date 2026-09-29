// @anchor: v3_edit_probe_intro
// v3 编辑往返探针：验证 insert / read / delete 与「编辑后索引自动刷新」
// 实测要点：insert(after) 紧贴锚点行插入，会把锚点原描述行挤到插入内容之后（描述归属随之改变）；
//           insert(before) 不影响锚点描述归属；delete 只保留两端锚点行，区间内的描述/空行会被一并删除。
//           本文件每个用例结束后用 write_file 复原为下面这份基准内容。

const base = 1;

// @anchor: v3_edit_start
// 区间起点（保留）
const a = base + 1;

// @anchor: v3_edit_end
// 区间终点（保留）
const b = a + 1;
