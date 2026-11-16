# 神策数据统计并发送到钉钉

从神策数据使用 Impala 查询 `pay_order` 事件数量，统计最近 4 个完整自然日的数据，并将汇总结果发送到钉钉群。项目使用 Python 编写，可在本地手动运行，也可以使用 GitHub Actions 定时运行。

> 当前查询的表名为 `events`，事件名为 `pay_order`。请先确认你的神策/Impala 环境中表结构、字段名和连接方式与代码相符。

## 工作流程

1. 连接到配置的 Impala 主机和数据库。
2. 按 `REPORT_TIMEZONE` 统计最近 4 个完整自然日的 `pay_order` 数量。
3. 使用钉钉自定义机器人发送文本汇总。

## 环境要求

- Python 3.10 或更高版本（代码使用 `zoneinfo` 和 `str | None` 类型语法）。
- 可访问 Impala 服务的网络，以及相应的连接信息和查询权限。
- 钉钉群自定义机器人及其 Webhook Token；如果机器人启用了加签，还需要加签密钥。

## 本地运行

### 1. 下载项目并进入目录

```bash
git clone https://github.com/hbktt1314-creator/sensors-dingtalk-report.git
cd sensors-dingtalk-report

### 2. 创建虚拟环境并安装依赖
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell：使用下面这行代替上面的 source 命令
# .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

### 2. 设置环境变量

export IMPALA_HOST="你的Impala主机地址"
export DINGTALK_ACCESS_TOKEN="钉钉机器人Webhook中的access_token"

# 可选：不设置时使用代码默认值，或不启用该功能
export IMPALA_PORT="21099"
export IMPALA_USER="sc_cluster"
export IMPALA_DATABASE="raw_data"
export IMPALA_PASSWORD="数据库密码"
export DINGTALK_SECRET="钉钉机器人加签密钥"
export DINGTALK_AT_MOBILES="手机号1,手机号2"
export REPORT_TIMEZONE="Asia/Shanghai"

3. 设置环境变量
将下面的占位内容替换为你自己的配置。不要把真实密码、Token 或加签密钥提交到 GitHub。

macOS / Linux（在运行程序的同一个终端窗口中执行）：

bash
export IMPALA_HOST="你的Impala主机地址"
export DINGTALK_ACCESS_TOKEN="钉钉机器人Webhook中的access_token"

# 可选：不设置时使用代码默认值，或不启用该功能
export IMPALA_PORT="21099"
export IMPALA_USER="sc_cluster"
export IMPALA_DATABASE="raw_data"
export IMPALA_PASSWORD="数据库密码"
export DINGTALK_SECRET="钉钉机器人加签密钥"
export DINGTALK_AT_MOBILES="手机号1,手机号2"
export REPORT_TIMEZONE="Asia/Shanghai"
Windows PowerShell 可这样设置（同样只对当前终端会话有效）：

PowerShell
$env:IMPALA_HOST = "你的Impala主机地址"
$env:DINGTALK_ACCESS_TOKEN = "钉钉机器人Webhook中的access_token"
$env:IMPALA_PORT = "21099"
$env:IMPALA_USER = "sc_cluster"
$env:IMPALA_DATABASE = "raw_data"
$env:IMPALA_PASSWORD = "数据库密码"
$env:DINGTALK_SECRET = "钉钉机器人加签密钥"
$env:DINGTALK_AT_MOBILES = "手机号1,手机号2"
$env:REPORT_TIMEZONE = "Asia/Shanghai"
必填：

变量	说明
IMPALA_HOST	Impala 服务主机名或 IP 地址
DINGTALK_ACCESS_TOKEN	钉钉自定义机器人的 Webhook Token
可选（不设置时使用代码默认值或关闭对应功能）：

变量	默认值/行为	说明
IMPALA_PORT	21099	Impala 服务端口
IMPALA_USER	sc_cluster	Impala 用户名
IMPALA_DATABASE	raw_data	查询所用数据库
IMPALA_PASSWORD	不设置	数据库密码；仅在连接需要密码时设置
DINGTALK_SECRET	不设置	钉钉机器人加签密钥；机器人启用加签时设置
DINGTALK_AT_MOBILES	不 @ 任何人	逗号分隔的手机号列表
REPORT_TIMEZONE	Asia/Shanghai	用于计算自然日的时区，例如 Asia/Shanghai
程序目前直接读取系统环境变量，不会自动加载 .env 文件。仓库的 .gitignore 已忽略 .env，但忽略文件不等同于加密；仍不要将秘密提交到仓库。

4. 运行
确认必填变量已设置后执行：

bash
python report.py
成功时会在终端看到“钉钉消息发送成功”，并在目标群收到统计消息。程序查询最近 4 个已经完整结束的自然日，不包含当天。

使用 GitHub Actions 定时运行
GitHub Actions 运行器也需要能够访问你的 Impala 服务。如果 Impala 只能从公司内网访问，GitHub 托管运行器通常无法连接；请使用经组织批准、可访问该服务的自托管运行器，或在可访问 Impala 的环境中本地运行。

1. 添加 Actions Secrets
打开仓库 Settings → Secrets and variables → Actions → New repository secret，添加：

必填：IMPALA_HOST、DINGTALK_ACCESS_TOKEN
按实际情况添加：IMPALA_PORT、IMPALA_USER、IMPALA_DATABASE、IMPALA_PASSWORD、DINGTALK_SECRET、DINGTALK_AT_MOBILES
Secrets 的名称要与下面 workflow 中的名称一致。不要把秘密写入 workflow 文件。

2. 添加定时任务文件
在仓库创建 .github/workflows/report.yml，内容如下：

YAML
name: Sensors DingTalk Report

on:
  # 每天 UTC 01:00（中国标准时间约 09:00）；定时运行可能有延迟。
  schedule:
    - cron: "0 1 * * *"
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run report
        env:
          IMPALA_HOST: ${{ secrets.IMPALA_HOST }}
          # 设置为固定默认值，避免未配置 Secret 时得到空字符串。
          IMPALA_PORT: "21099"
          IMPALA_USER: ${{ secrets.IMPALA_USER }}
          IMPALA_DATABASE: ${{ secrets.IMPALA_DATABASE }}
          IMPALA_PASSWORD: ${{ secrets.IMPALA_PASSWORD }}
          DINGTALK_ACCESS_TOKEN: ${{ secrets.DINGTALK_ACCESS_TOKEN }}
          DINGTALK_SECRET: ${{ secrets.DINGTALK_SECRET }}
          DINGTALK_AT_MOBILES: ${{ secrets.DINGTALK_AT_MOBILES }}
          REPORT_TIMEZONE: Asia/Shanghai
        run: python report.py
如果在 Actions 中设置了可选变量的 Secret，建议填写实际值；若 Secrets 未设置，GitHub 会提供空值，程序对 IMPALA_PORT 使用默认值的逻辑要求该变量未设置。最简单的做法是：不要创建 IMPALA_PORT Secret（或在 workflow 中写固定值 IMPALA_PORT: "21099"）；IMPALA_USER 和 IMPALA_DATABASE 可分别固定为 sc_cluster 和 raw_data。其他可选项为空时会按代码行为处理。

完成后进入仓库 Actions 页面，选择 Sensors DingTalk Report，点击 Run workflow 手动测试。之后 workflow 会按 cron 计划运行。GitHub Actions 的 cron 使用 UTC，不是北京时间。

常见问题排查
提示缺少 IMPALA_HOST 或 DINGTALK_ACCESS_TOKEN：检查变量是否在当前终端中设置；Actions 运行时则检查 Secrets 名称及 workflow 映射是否一致。
Impala 连接超时或被拒绝：检查主机、端口、网络/VPN、防火墙和账号权限。GitHub 托管运行器无法直接访问你的私有内网。
ValueError 转换端口失败：检查 IMPALA_PORT 是否为空或包含非数字字符；如在 Actions 使用可选 Secret，可在 workflow 中固定填写 21099。
钉钉返回发送失败或加签错误：确认机器人 Token；若启用了加签，设置正确的 DINGTALK_SECRET。也要检查机器人安全策略是否允许该消息。
查询结果为 0 或日期不对：核对 events 表、date 字段格式、事件名 pay_order 和 REPORT_TIMEZONE。查询使用 Impala 的 unix_timestamp(date) 转换，请确认该表达式适用于你的字段格式。
没有收到 @ 提醒：确认 DINGTALK_AT_MOBILES 中手机号格式正确，并且该成员在群里；不需要提醒时可不配置。
Actions 没有按时启动：cron 采用 UTC，且 GitHub 定时任务可能延迟；检查 workflow 文件路径必须是 .github/workflows/ 下的 YAML 文件，并查看 Actions 页面中的运行记录。
安全提醒
不要在公开仓库提交数据库密码、钉钉 Token、加签密钥或个人信息。
如果秘密曾经提交到 Git 历史，即使后来删除文件，也应立即在对应服务中撤销并重新生成该秘密。
只授予机器人和数据库账号完成任务所需的最小权限。
Code

GitHub Actions workflow 文件：

```yaml
name: Sensors DingTalk Report

on:
  # 每天 UTC 01:00（中国标准时间约 09:00）；定时运行可能有延迟。
  schedule:
    - cron: "0 1 * * *"
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run report
        env:
          IMPALA_HOST: ${{ secrets.IMPALA_HOST }}
          IMPALA_PORT: "21099"
          IMPALA_USER: ${{ secrets.IMPALA_USER }}
          IMPALA_DATABASE: ${{ secrets.IMPALA_DATABASE }}
          IMPALA_PASSWORD: ${{ secrets.IMPALA_PASSWORD }}
          DINGTALK_ACCESS_TOKEN: ${{ secrets.DINGTALK_ACCESS_TOKEN }}
          DINGTALK_SECRET: ${{ secrets.DINGTALK_SECRET }}
          DINGTALK_AT_MOBILES: ${{ secrets.DINGTALK_AT_MOBILES }}
          REPORT_TIMEZONE: Asia/Shanghai
        run: python report.py
建议 Python 版本：

3.10 以上，最稳妥
3.11 也可
3.12 也通常可用，但 impyla/thrift 兼容性有时受影响，实际环境更推荐 3.10 或 3.11
