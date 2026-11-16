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
