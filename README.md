# Benchmark Engineer 考核任务

## 背景
我们需要构建一套用于评估 AI 编程能力的测试集。你的任务是创建一个完整的 Benchmark Task。

## 题目要求
请创建一个名为 `csv-cleaner-cli` 的任务。
**场景**：AI 需要编写一个 Python 命令行工具，用于清洗脏乱的 CSV 数据。

## 你的交付物
请提交一个压缩包，包含以下目录结构（严格遵守）：
csv-cleaner-cli/
├── task.toml                 # [必填] 按照 V1.0 规范填写元数据，参考测试题中的 task.toml 文件
├── instruction.md            # [必填] 清晰的英文题目描述
├── environment/              # [必填]
│   ├── Dockerfile            # 必须锁定 Python 版本
│   └── dirty_data.csv        # 初始的脏数据（请自己构造）
├── solution/                 # [必填]
│   ├── cleaner.py            # 标准答案代码
│   └── solve.sh              # 运行答案的脚本
└── tests/                    # [核心]
    ├── test_logic.py         # 验证逻辑
    └── test.sh               # 测试入口 (必须返回 exit code 0 或 1)

## 关于测试文件的职责
- `test_logic.py` 的核心作用是验证你编写的 `cleaner.py` 是否真的完成了数据清洗任务。
- 它应基于你构造的 `dirty_data.csv`，验证你用`cleaner.py`处理后的输出结果是否正确，例如是否完成了去空行、去重、字段清理、非法值处理等。
- `test.sh` 是测试启动脚本，用来执行整个验证流程。通常它会负责准备环境、调用 `test_logic.py`，并最终以 `0` 表示通过、`1` 表示失败。

## 评分标准
1. **可运行性**：我们会在纯净的 Linux 环境下执行 `docker build`, `tests/test.sh` 和 `solution/solve.sh`，必须一次跑通。
  1.1. 工作目录为instruction.md所在目录.
  1.2. 必须将此项目的所有文件一起COPY到docker image中.
  1.3. test.sh必须返回 exit code 0 或 1.
2. **鲁棒性**：你的测试脚本必须能拦截“错误答案”（例如：如果 AI 只是复制了文件没做清洗，测试必须报错）。
3. **规范性**：`task.toml` 填写是否完整，Dockerfile 是否锁定了版本。
4. **数据构造能力**：`dirty_data.csv` 是否包含足够的边界情况（如空行、非法字符）。

## 提交方式
请将文件夹打包为 `yourname_assessment.zip` 发送回邮件。