from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware

from saltbox_metric import __version__
from saltbox_metric.config import APP_DESC, APP_NAME, SETTINGS, logger
from saltbox_sdk.config.discovery_config import DISCOVERY_SETTINGS
from saltbox_sdk.db.redis.config import POOL
from saltbox_sdk.discovery_client.client import DiscoveryClient
from saltbox_sdk.discovery_client.schemas import HealthCheckResponse
from saltbox_sdk.fastapi_utils.custom_openapi import custom_openapi, patch_swagger_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    discovery_client = DiscoveryClient(
        openapi_schema=app.openapi(),
        # httpx_client=get_httpx_async_client(),
    )
    await discovery_client.register()

    yield
    await POOL.aclose()


app_config: dict[str, Any] = {
    'title': APP_NAME,
    'lifespan': lifespan,
    'version': __version__,
    'description': APP_DESC,
    'root_path': SETTINGS.base_url_root_path,
    'healthcheck_path': '/discovery/health',
    # 'docs_url': '/docs', # or None to disable
    # 'openapi_url': '/openapi.json', # or None to disable
}

app_config = patch_swagger_config(app_config)
app = FastAPI(**app_config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/discovery/health')
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status='ok',
        message=f'Instance of {DISCOVERY_SETTINGS.service_name} is running',
    )


@app.exception_handler(exc_class_or_status_code=HTTPException)
async def logged_http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Custom exception handler for HTTP exceptions with logging"""
    logger.exception(f'HTTP Exception: {request.url.path}: {exc}', exc_info=True)
    return await http_exception_handler(request, exc)


app.openapi = partial(custom_openapi, app, app_config, servers=[{'url': SETTINGS.base_url_root_path}])  # type: ignore[method-assign]
