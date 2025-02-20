
from elasticsearch import AsyncElasticsearch

from ...config import config


class ESClient:

    def __init__(self):
        self.es = None

    def get_es_client(self) -> AsyncElasticsearch:
        es = AsyncElasticsearch(
            f'https://{config.credentials.es.host}:{config.credentials.es.port}/',
            basic_auth=(config.credentials.es.username, config.credentials.es.password),
            ca_certs=config.credentials.es.ca_cert_path, request_timeout=60, retry_on_timeout=True
        )
        return es

    # async context manager:
    async def __aenter__(self):
        self.es = self.get_es_client()
        return self.es
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.es.close()
        self.es = None
        return False



