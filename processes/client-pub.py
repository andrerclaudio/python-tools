#!/usr/bin/env python3
import asyncio
import logging
import sys

from amqtt.client import MQTTClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("minibroker")

BROKER_CONFIG = {
    "listeners": {"default": {"type": "tcp", "bind": "127.0.0.1:1883"}},
}


async def publish_once(topic: str, payload: str, qos: int = 0) -> None:
    client = MQTTClient()
    try:
        await client.connect("mqtt://127.0.0.1:1883/")
        await client.publish(topic, payload.encode("utf-8"), qos=qos)
        logger.info("Published to %s: %s", topic, payload)
        await client.disconnect()
    except Exception as exc:
        logger.exception("Publish failed: %s", exc)


if __name__ == "__main__":
    try:
        asyncio.run(publish_once(topic="demo/topic", payload="Test on PUB", qos=2))

    except KeyboardInterrupt:
        sys.exit(0)
