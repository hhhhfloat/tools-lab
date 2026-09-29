// search 语料：alpha 模块（调用链顶端）
// 预期: search_text(path='tools-lab/search') 对 'alphaFn' 命中本文件定义行 + app.js 调用行
function alphaFn(x) {
  return betaFn(x) + gammaFn(x);
}

module.exports = { alphaFn };
