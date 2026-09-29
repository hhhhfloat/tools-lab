// @anchor: edit_target_intro
// 编辑测试目标：提供一对 start/end 锚点，用于 read/insert/delete 的区间操作
export const scratch = [];

// @anchor: edit_target_scratch_start
// 可删除区起点
const tmpA = 1;
const tmpB = 2;
const tmpC = 3;

// @anchor: edit_target_inserted
// 由 insert_at_anchor 插入的锚点
export const inserted = 1;


// @anchor: edit_target_scratch_end
// @anchor: edit_target_tail
// 尾部锚点
export const done = true;
