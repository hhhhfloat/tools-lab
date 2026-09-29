// @anchor: rt_intro
// 区间编辑回归探针：start/end 成对，用于 insert→read→delete 往返验证
// 注意：区间删除只保留两端锚点行，起点锚点的描述行与空行位于区间内会被一并删除

const RT_BASE = 0;

// @anchor: rt_start
// 区间起点（本描述行会被区间删除吃掉）

// @anchor: rt_end
// 区间终点
