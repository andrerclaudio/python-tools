#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from amqtt.broker import Broker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("minibroker")

BROKER_CONFIG = {
    "listeners": {"default": {"type": "tcp", "bind": "127.0.0.1:1883"}},
}


async def run_broker() -> None:
    broker: Broker = Broker(BROKER_CONFIG)
    try:
        logger.info("Starting broker on 127.0.0.1:1883")
        await broker.start()
        # wait until cancelled by signal
        stop = asyncio.Event()
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                asyncio.get_running_loop().add_signal_handler(s, stop.set)
            except NotImplementedError:
                pass
        await stop.wait()
    except Exception as exc:
        logger.exception("Broker error: %s", exc)
    finally:
        try:
            logger.info("Shutting down broker")
            await broker.shutdown()
        except Exception:
            logger.exception("Error shutting down broker")


if __name__ == "__main__":
    try:
        asyncio.run(run_broker())

    except KeyboardInterrupt:
        sys.exit(0)
