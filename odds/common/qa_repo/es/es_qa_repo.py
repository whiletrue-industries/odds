from typing import Optional, List
from hashlib import sha256

from elasticsearch import Elasticsearch
import elasticsearch

from ..qa_repo import QARepo, QA
from ...datatypes import Embedding
from ...realtime_status import realtime_status as rts
from ...embedder import embedder

from ...metadata_store.es.es_client import ESClient

ES_INDEX = 'qa'

class ESQARepo(QARepo):

    def __init__(self):
        self.initialized = False

    async def single_time_init(self, client: Elasticsearch):
        if self.initialized:
            return
        self.initialized = True
        assert await client.ping()
        if not await client.indices.exists(index=ES_INDEX):
            await client.indices.create(index=ES_INDEX, body={
                'mappings': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'question': {'type': 'text'},
                        'answer': {'type': 'text'},
                        'success': {'type': 'boolean'},
                        'score': {'type': 'integer'},
                        'embeddings': {
                            'type': 'dense_vector',
                            'dims': embedder.vector_size(),
                            'index': True,
                            'similarity': 'cosine'
                        }
                    }
                }
            })

    def toQa(self, data):
        data = dict(data)
        data = dict((k, v) for k, v in data.items() if k in QA.__dataclass_fields__)
        return QA(**data)
    
    def getId(self, question: str) -> str:
        question = question.strip().lower()
        question = '_'.join(question.split())
        question = question.encode()
        return sha256(question).hexdigest()[:16]

    async def storeQA(self, question: str, answer: str, success: bool, score: int) -> QA:
        async with ESClient() as client:
            await self.single_time_init(client)
            id = self.getId(question)
            body = dict(
                id=id,
                question=question,
                answer=answer,
                success=success,
                score=score,
                embeddings=(await embedder.embed(question)).tolist()
            )
            await client.create(index=ES_INDEX, id=id, body=body)
            return self.toQa(body)

    async def getQuestion(self, *, question: str=None, id: str=None) -> Optional[QA]:
        assert question or id
        if not id:
            id = self.getId(question)
        async with ESClient() as client:
            try:
                await self.single_time_init(client)
                data = await client.get(index=ES_INDEX, id=id)
                data = data.get('_source')
                if not data:
                    return None
                return self.toQa(data)
            except elasticsearch.NotFoundError as e:
                pass
        return None
    
    async def findRelated(self, question: str, own_id: str) -> List[QA]:
        async with ESClient() as client:
            await self.single_time_init(client)
            embedding = await embedder.embed(question)
            knn = {
                'field': 'embeddings',
                'query_vector': embedding.tolist(),
                'k': 5,
                'num_candidates': 50,
                'boost': 0.8,
                'filter': {
                    'bool': {
                        'must': [
                            {
                                'bool': {
                                    'must_not': {
                                        'term': {'id': own_id}
                                    }
                                }
                            },
                            {
                                'bool': {
                                    'must_not': {
                                        'term': {'success': False}
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            query = {
                'bool': {
                    'must': [
                        {
                            'multi_match': {
                                'query': question,
                                'fields': ['question', 'answer'],
                                'boost': 0.2,
                                'type': 'cross_fields',
                                'operator': 'or',
                            }
                        },
                        {
                            'bool': {
                                'must_not': {
                                    'term': {'id': own_id}
                                }
                            }
                        },
                        {
                            'bool': {
                                'must_not': {
                                    'term': {'success': False}
                                }
                            }
                        }
                    ]
                }
            }
            ret = await client.search(index=ES_INDEX, query=query, knn=knn, size=5, min_score=1)
            qas = []
            for hit in ret.get('hits', {}).get('hits', []):
                if hit.get('_source'):
                    qa = self.toQa(hit['_source'])
                    # qa.score = hit.get('_score')
                    qas.append(qa)
            return qas
        return []
        
    async def getEmbedding(self, question: str) -> Embedding:
        return await embedder.embed(question)

