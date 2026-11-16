# sensors-dingtalk-report
从神策数据查询统计指标，并定时发送到钉钉群的自动化工具。

# 项目本地运行
export IMPALA_HOST="你的Impala地址"

export DINGTALK_ACCESS_TOKEN="钉钉机器人Token"

export IMPALA_PORT="你的Impala端口"

export IMPALA_USER="sc_cluster"

export IMPALA_DATABASE="raw_data"

export IMPALA_PASSWORD="数据库密码"

export DINGTALK_SECRET="钉钉机器人加签密钥"

export DINGTALK_AT_MOBILES="手机号1,手机号2"

export REPORT_TIMEZONE="Asia/Shanghai"

python report.py
