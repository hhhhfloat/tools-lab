-- @anchor: schema_sql_dash_style
-- 预期: 该写法不被识别（锚点正则不含 SQL 的 -- 注释）
CREATE TABLE items (
  id INTEGER PRIMARY KEY,
  name TEXT
);

/* @anchor: schema_sql_block_style */
/* 预期: 该写法可被识别（块注释形式） */
CREATE INDEX idx_items_name ON items(name);
