import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, time as datetime_time, timedelta
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import requests
from impala.dbapi import connect


def required_env(name: str) -> str:
    """读取必需环境变量；缺少时给出明确错误。"""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少必需的环境变量：{name}")
    return value


class DataDiver:
    def __init__(self):
        self.host = required_env("IMPALA_HOST")
        self.port = int(os.getenv("IMPALA_PORT", "21099"))
        self.user = os.getenv("IMPALA_USER", "sc_cluster")
        self.database = os.getenv("IMPALA_DATABASE", "raw_data")
        self.password = os.getenv("IMPALA_PASSWORD")

    def get_daily_counts(self, days: int = 4) -> dict[str, int]:
        """查询过去 days 个完整自然日的 pay_order 数量。"""
        timezone = ZoneInfo(os.getenv("REPORT_TIMEZONE", "Asia/Shanghai"))
        today = datetime.now(timezone).date()

        counts = {}
        connection_args = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "database": self.database,
        }
        if self.password:
            connection_args["password"] = self.password

        with connect(**connection_args) as conn:
            with conn.cursor() as cursor:
                for offset in range(1, days + 1):
                    day = today - timedelta(days=offset)
                    start = datetime.combine(day, datetime_time.min, tzinfo=timezone)
                    end = start + timedelta(days=1)

                    start_ts = int(start.timestamp())
                    end_ts = int(end.timestamp())

                    # 使用 [当天开始, 次日开始) 的范围，避免只查到 00:00:00。
                    sql = f"""
                        SELECT COUNT(1)
                        FROM events
                        WHERE unix_timestamp(`date`) >= {start_ts}
                          AND unix_timestamp(`date`) < {end_ts}
                          AND event = 'pay_order'
                    """
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    counts[day.isoformat()] = int(row[0] or 0)

        return counts


def dingtalk_signed_params(token: str, secret: str | None) -> dict[str, str]:
    """生成钉钉自定义机器人请求参数；配置了加签密钥时自动签名。"""
    params = {"access_token": token}

    if secret:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        digest = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = quote_plus(base64.b64encode(digest).decode("utf-8"))

        params.update({"timestamp": timestamp, "sign": sign})

    return params


def send_to_dingtalk(content: str) -> None:
    token = required_env("DINGTALK_ACCESS_TOKEN")
    secret = os.getenv("DINGTALK_SECRET")
    mobiles = [
        mobile.strip()
        for mobile in os.getenv("DINGTALK_AT_MOBILES", "").split(",")
        if mobile.strip()
    ]

    payload = {
        "msgtype": "text",
        "text": {"content": content},
        "at": {
            "atMobiles": mobiles,
            "isAtAll": False,
        },
    }

    response = requests.post(
        "https://oapi.dingtalk.com/robot/send",
        params=dingtalk_signed_params(token, secret),
        json=payload,
        timeout=10,
    )
    response.raise_for_status()

    try:
        result = response.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError("钉钉返回了无法解析的响应") from exc

    if result.get("errcode") != 0:
        raise RuntimeError(
            f"钉钉发送失败：errcode={result.get('errcode')}，"
            f"errmsg={result.get('errmsg')}"
        )


def main():
    counts = DataDiver().get_daily_counts(days=4)

    lines = ["统计近四天神策 pay_order 数据量："]
    for day, count in sorted(counts.items()):
        lines.append(f"{day}：{count}")

    message = "\n".join(lines)
    send_to_dingtalk(message)
    print("钉钉消息发送成功")


if __name__ == "__main__":
    main()