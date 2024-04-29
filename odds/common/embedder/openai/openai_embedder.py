import httpx
import numpy as np
import math

from ...datatypes import Embedding

from ..embedder import Embedder
from ...config import config
from ...retry import Retry


class OpenAIEmbedder(Embedder):

    MODEL = 'text-embedding-3-small'
    VECTOR_SIZE = 1536
    COST = 0.02/1000000

    def __init__(self):
        super().__init__()
        self.total_usage = 0
        self.cost = 0

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
                self.total_usage += result['usage']['total_tokens']
                cost = self.COST * result['usage']['total_tokens']
                if math.ceil(self.cost) != math.ceil(self.cost + cost):
                    self.print_total_usage()
                self.cost += cost
            if result.get('data') and result['data'][0].get('object') == 'embedding' and result['data'][0]['embedding']:
                vector: list[float] = result['data'][0]['embedding']
                embedding: Embedding = np.array(vector, dtype=np.float32)
                return embedding
            return None
    
    def print_usage(self, total_tokens, cost):
        print('OpenAI Embedding usage:', total_tokens)
        print('OpenAI Embedding cost:', f'$ {cost:.2f}')

    def print_total_usage(self):
        self.print_usage(self.total_usage, self.cost)

    def vector_size(self) -> int:
        return self.VECTOR_SIZE