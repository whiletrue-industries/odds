from httpx import AsyncClient
from arq.connections import RedisSettings

from odds.backend import backend

REDIS_SETTINGS = RedisSettings(host='redis')

async def scan_specific(ctx, catalogId, datasetId, force):
    await ctx['backend'].scan_specific(catalogId=catalogId, datasetId=datasetId, force=force)

async def startup(ctx):
    ctx['session'] = AsyncClient()
    ctx['backend'] = backend.ODDSBackend()

async def shutdown(ctx):
    await ctx['session'].aclose()
    del ctx['backend']

class WorkerSettings:
    functions = [scan_specific]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = REDIS_SETTINGS
