# -*- coding: utf-8 -*-
import base64
import json
import logging
import os
from urllib.parse import parse_qs

import requests

logger = logging.getLogger()


def handler(event, context):
    logger.info("接收到的event: %s", event)

    # event为bytes转换为dict
    try:
        event_json = json.loads(event)
    except:
        return "The request did not come from an HTTP Trigger because the event is not a json string, event: {}".format(
            event)

    # 判断是否有body
    if "body" not in event_json:
        return "The request did not come from an HTTP Trigger because the event does not include the 'body' field, event: {}".format(
            event)

    url_path = event_json.get('rawPath', "")

    webhook_kind = url_path.split('/')[2]
    logger.info("url中webhook类型为: %s", webhook_kind)

    # 根据url path判断是那种类型告警
    match webhook_kind:
        case "discord":
            logger.info("webhook类型为discord")
            return process_event_discrod(event_json)
        case _:
            logger.info("未知webhook类型")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'text/plain'},
                'isBase64Encoded': False,
                'body': {'message': '未知的webhook类型'}
            }


def process_event_discrod(event):
    logger.info("开始discord webhook...")

    req_header = event['headers']
    logger.info("接收到的headers: %s", req_header)

    # 判断body是否为空
    req_body = event['body']

    if not req_body:
        logger.info("本次接收到的body为空")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'isBase64Encoded': False,
            'body': {
                'message': 'body is empty'
            }
        }

    # 判断body是否为base64编码数据
    if 'isBase64Encoded' in event and event['isBase64Encoded']:
        logger.info("开始解码Base64内容")
        req_body = base64.b64decode(req_body).decode("utf-8")
        params = parse_qs(req_body)
    else:
        params = req_body

    logger.info("接收到的body: %s", params)

    discord_webhook = os.environ.get('DISCORD_URL')

    # 发送消息到keep
    response = send_to_webhook(discord_webhook, params)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'isBase64Encoded': False,
        'body': response
    }


# 发送消息到keep
def send_to_webhook(url, message):
    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=message)

    logger.info("消息转发到discord成功")

    logger.info(response.json())

    return response.json()
