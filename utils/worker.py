from httpx import AsyncClient
from arq.connections import RedisSettings
from arq.worker import create_pool

from odds.backend import backend
from odds.backend.processor import dataset_processor
import logging

REDIS_SETTINGS = RedisSettings(host='redis')


async def scan_specific(ctx, catalogId, datasetId, force):
    await ctx['backend'].scan_specific(catalogId=catalogId, datasetId=datasetId, force=force, use_pool=ctx['redis'])

async def dataset_processor_process(ctx, *args, **kwargs):
    await dataset_processor.process(*args, **kwargs)

async def startup(ctx):
    ctx['session'] = AsyncClient()
    ctx['backend'] = backend.ODDSBackend()
    ctx['redis'] = await create_pool(REDIS_SETTINGS)
    logger = logging.getLogger('arq.worker')
    logger.setLevel(logging.INFO)

async def shutdown(ctx):
    await ctx['session'].aclose()
    del ctx['backend']

class WorkerSettings:
    functions = [
        scan_specific,
        dataset_processor_process
        # func()
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS
    job_timeout = 86400
    keep_result = 60

