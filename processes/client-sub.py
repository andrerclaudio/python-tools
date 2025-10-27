#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys
from typing import Optional
from time import sleep

from amqtt.broker import Broker
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


async def subscribe_forever(topic: str, qos: int = 0) -> None:
    client = MQTTClient()
    try:
        await client.connect("mqtt://127.0.0.1:1883/")
        await client.subscribe([(topic, qos)])
        logger.info("Subscribed to %s", topic)
        while True:
            try:
                message = await client.deliver_message()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error receiving message; will continue")
                continue
            if message is None:
                continue
            packet = message.publish_packet
            payload = packet.payload.data.decode("utf-8", errors="replace")
            logger.info(
                "Received on %s: %s", packet.variable_header.topic_name, payload
            )
    except Exception as exc:
        logger.exception("Subscriber failed: %s", exc)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(subscribe_forever(topic="demo/topic", qos=2))

    except KeyboardInterrupt:
        sys.exit(0)
