# csv-scope

`csv-scope` 是一个面向数据工程、运营分析和后端批处理的 CSV 数据质量 CLI。它不是一个演示脚本，而是可以放进本地开发、CI、ETL 前置检查或数据交付验收里的轻量工具：扫描 CSV，生成可读报告，并按 JSON expectations 做质量门禁。

项目只依赖 Python 标准库，Python 3.10+ 即可运行。

## 适合场景

- 在导入 CRM、订单、账单、埋点日志前快速检查 CSV 是否可信。
- 在 CI 中阻止缺列、类型漂移、缺失率超标的数据文件合入。
- 给产品、运营或客户交付 Markdown 数据质量摘要。
- 给数据管道输出 JSON profile，供后续脚本或监控系统读取。

## 功能

- 自动读取带表头的 CSV 文件。
- 推断列类型：`number`、`date`、`boolean`、`text`、`empty`。
- 统计行数、列数、缺失值数量、缺失率、唯一值数量。
- 计算数值列 `min`、`p25`、`median`、`p75`、`max`。
- 使用 IQR 方法提示数值异常值。
- 识别日期列最早/最晚日期。
- 输出每列 top values，帮助发现脏枚举和拼写漂移。
- 支持 JSON 和 Markdown 报告。
- 支持 JSON expectations：必需列、期望类型、最大缺失率、最大异常值数量。
- 支持 `--fail-on` 控制退出码，可直接用于 CI 和数据管道。

## 快速开始

无需安装：

```bash
python -m csv_scope examples/sample.csv --format markdown
```

安装为命令：

```bash
python -m pip install -e .
csv-scope examples/sample.csv --format json
```

保存报告：

```bash
csv-scope examples/sample.csv --format markdown --output report.md
```

用 expectations 做质量门禁：

```bash
csv-scope examples/sample.csv \
  --expectations examples/expectations.json \
  --format markdown \
  --fail-on error
```

退出码：

- `0`：没有达到 `--fail-on` 指定级别的问题。
- `1`：expectations 检查出现需要失败的问题。
- `2`：命令行参数错误，由 `argparse` 返回。

## Expectations 示例

```json
{
  "required_columns": ["customer_id", "created_at", "amount", "status"],
  "columns": {
    "customer_id": { "type": "number", "max_missing_rate": 0 },
    "created_at": { "type": "date", "max_missing_rate": 0 },
    "amount": { "type": "number", "max_missing_rate": 0.05, "max_outlier_count": 2 },
    "status": { "type": "text", "max_missing_rate": 0.01 }
  }
}
```

`examples/expectations.json` 与示例 CSV 匹配，会通过检查。`examples/failing-expectations.json` 用于演示失败报告和非零退出码。

更多细节见 [docs/USAGE.md](docs/USAGE.md) 和 [docs/OUTPUT.md](docs/OUTPUT.md)。

## 命令行参数

```text
usage: python -m csv_scope [-h] [--format {json,markdown}]
                           [--encoding ENCODING] [--delimiter DELIMITER]
                           [--output OUTPUT] [--expectations EXPECTATIONS]
                           [--fail-on {never,error,warning}]
                           [--top-values TOP_VALUES]
                           csv_file
```

常用参数：

- `csv_file`：要体检的 CSV 文件路径。
- `--format`：输出格式，支持 `json` 和 `markdown`，默认 `markdown`。
- `--encoding`：文件编码，默认 `utf-8-sig`。
- `--delimiter`：CSV 分隔符，默认 `,`。
- `--output`：报告输出文件路径；未指定时输出到终端。
- `--expectations`：JSON 质量契约路径。
- `--fail-on`：`never`、`error` 或 `warning`，默认 `error`。
- `--top-values`：每列输出多少个高频值，默认 `5`。

## CI 用法

```yaml
name: data-quality
on: [push, pull_request]
jobs:
  csv-scope:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e .
      - run: csv-scope examples/sample.csv --expectations examples/expectations.json --format json
```

## 开发

```bash
python -m compileall -q csv_scope tests
python tests/test_profiler.py
python -m pytest
```

`pytest` 只用于开发测试；运行时不需要第三方依赖。

## 限制

- 当前只处理有表头的 CSV。
- 类型推断是启发式规则，目标是发现问题而不是替代数据库 schema。
- 大文件会读入内存；百万行级文件建议先采样或后续接入 streaming 模式。
- 日期格式覆盖常见格式，特殊本地化格式需要先清洗。

## 许可

MIT License
