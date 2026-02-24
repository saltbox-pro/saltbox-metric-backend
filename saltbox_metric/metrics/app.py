import asyncio
import json

from prometheus_client import CollectorRegistry

from saltbox_metric.config import logger
from saltbox_metric.metrics.service.metric_factory import MetricFactory
from saltbox_metric.metrics.service.metric_router import MetricRouter
from saltbox_metric.metrics.service.metric_service import start_prometheus_client
from saltbox_sdk.db.redis.config import get_redis_now

metric_registry = CollectorRegistry()


class MetricApp:
    def __init__(self) -> None:
        self.redis_client = get_redis_now()

        mf = MetricFactory(registry=metric_registry, redis_client=self.redis_client)
        metrics = mf.create_all()
        self.metric_router = MetricRouter(metrics=metrics)

    async def start(self) -> None:

        logger.info('Starting metric app')
        await start_prometheus_client(registry=metric_registry)

        ps = self.redis_client.pubsub()
        await ps.psubscribe('metrics:*')

        async for message in ps.listen():
            if message and message['type'] == 'pmessage':
                logger.debug('Received metric message: %s', message)

                await self.metric_router.route_and_aggregate(
                    tag=message['channel'].decode(),
                    data=json.loads(message['data'].decode()),
                )
            await asyncio.sleep(0.00001)


async def async_main() -> None:
    app = MetricApp()
    await app.start()


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt: # NOTE: Unnecessary traceback for dev mode
        pass

if __name__ == '__main__':
    main()
