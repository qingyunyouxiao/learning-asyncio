#!/usr/bin/env python3
import sys

def main():
    # 初始化空字符串，对应原代码的 s 和 sep
    s = ""
    sep = ""
    # 遍历命令行参数，从索引 1 开始（跳过脚本名）
    for arg in sys.argv[1:]:
        s += sep + arg
        sep = " "
    # 打印拼接后的结果
    print(s)

if __name__ == "__main__":
    main()