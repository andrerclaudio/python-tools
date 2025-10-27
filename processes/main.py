#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys

from amqtt.broker import Broker

# Initialize logger configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s"
)

LOG = logging.getLogger(__name__)


IP: str = "127.0.0.1"
PORT: int = 1883


BROKER_CONFIG = {
    "listeners": {"default": {"type": "tcp", "bind": f"{IP}:{PORT}"}},
}


async def run_broker() -> None:
    broker: Broker = Broker(BROKER_CONFIG)

    # create stop event and register signal handlers before starting the broker
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(s, stop.set)
        except NotImplementedError:
            # unlikely on Linux, but keeps compatibility
            pass

    try:
        LOG.info("Starting broker on %s:%d", IP, PORT)
        await broker.start()
        # wait until cancelled by a signal
        await stop.wait()

    except asyncio.CancelledError:
        # allow cooperative cancellation to bubble
        raise
    except Exception as exc:
        LOG.exception("Broker error: %s", exc)

    finally:
        try:
            LOG.info("Shutting down broker")
            await broker.shutdown()
        except Exception:
            LOG.exception("Error shutting down broker")


if __name__ == "__main__":
    try:
        asyncio.run(run_broker())
    except KeyboardInterrupt:
        sys.exit(0)
