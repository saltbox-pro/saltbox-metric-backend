import asyncio

from prometheus_client import CollectorRegistry, start_http_server

from saltbox_metric.config import SETTINGS, logger


async def start_prometheus_client(registry: CollectorRegistry) -> None:
    def run() -> None:
        port = SETTINGS.prometheus_client_port
        logger.info('Starting Prometheus metrics server on port %s', port)
        _ = start_http_server(
            port=port,
            addr=SETTINGS.prometheus_client_addr,
            registry=registry,
            certfile=SETTINGS.prometheus_client_certfile,
            keyfile=SETTINGS.prometheus_client_keyfile,
            client_cafile=SETTINGS.prometheus_client_cafile,
            client_capath=SETTINGS.prometheus_client_capath,
            client_auth_required=SETTINGS.prometheus_client_auth_required,
        )
        logger.info('Prometheus metrics server launched')

    await asyncio.to_thread(run)
