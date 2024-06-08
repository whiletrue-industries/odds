import httpx
import numpy as np
import math

from ...datatypes import Embedding

from ..embedder import Embedder
from ...cost_collector import CostCollector
from ...config import config
from ...retry import Retry


class OpenAIEmbedder(Embedder):

    MODEL = 'text-embedding-3-small'
    VECTOR_SIZE = 1536
    COST = 0.02/1000000

    def __init__(self):
        super().__init__()
        self.cost = CostCollector('openai', {'embed': {'tokens': self.COST}})

    async def embed(self, text: str) -> None:
        headers = {
            'Authorization': f'Bearer {config.credentials.openai.key}',
            'OpenAI-Organization': config.credentials.openai.org,
            'Content-Type': 'application/json'
        }
        request = dict(
            model=self.MODEL,
            input=text,
        )
        async with httpx.AsyncClient() as client:
            response = await Retry()(client, 'post',
                'https://api.openai.com/v1/embeddings',
                json=request,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            if result['usage']:
                self.cost.start_transaction()
                self.cost.update_cost('embed', 'tokens', result['usage']['total_tokens'])
                self.cost.end_transaction()
            if result.get('data') and result['data'][0].get('object') == 'embedding' and result['data'][0]['embedding']:
                vector: list[float] = result['data'][0]['embedding']
                embedding: Embedding = np.array(vector, dtype=np.float32)
                return embedding
            return None
    
    def print_total_usage(self):
        self.cost.print_total_usage()

    def vector_size(self) -> int:
        return self.VECTOR_SIZE