// @anchor: java_sub_control_probe
// 预期: 子目录下的 java 模式正常编译运行（v4 复核 D6 未复现）
public class Hello {
    public static void main(String[] args) {
        System.out.println("D6 probe: java mode in subdir");
    }
}
