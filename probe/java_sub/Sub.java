// @anchor: java_sub_nonpublic_probe
// 预期: 主类名按「文件名」推导 → 非 public 类名与文件名不一致时 java 运行会报 CNFE
class Other {
    public static void main(String[] args) {
        System.out.println("non-public class in Sub.java");
    }
}
