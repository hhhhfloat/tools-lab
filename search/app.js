// search 语料：应用入口，调用 alphaFn / betaFn / gammaFn
// 预期: 本文件含 alphaFn×1、betaFn×1、gammaFn×2、computeTotal 定义与调用
function computeTotal(list) {
  return alphaFn(betaFn(gammaFn(list)));
}

function computeMore(list) {
  return gammaFn(list) + computeTotal(list);
}

module.exports = { computeTotal, computeMore };
