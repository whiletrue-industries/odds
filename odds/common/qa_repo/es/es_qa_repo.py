from typing import Optional, List
from hashlib import sha256

from elasticsearch import Elasticsearch
import elasticsearch

from odds.common.retry import BaseRetry

from ..qa_repo import QARepo, QA, QAResult
from ...datatypes import Embedding
from ...realtime_status import realtime_status as rts
from ...embedder import embedder

from ...metadata_store.es.es_client import ESClient

ES_INDEX = 'qa'

class ESQARepo(QARepo):

    PAGE_SIZE = 20

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
                        'deployment_id': {'type': 'keyword'},
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
    
    def getId(self, question: str, deployment_id: str) -> str:
        question = question.strip().lower()
        question = '_'.join(question.split()) + f'__{deployment_id}'
        question = question.encode()
        return sha256(question).hexdigest()[:16]

    async def storeQA(self, question: str, answer: str, success: bool, score: int, deployment_id: str) -> QA:
        async with ESClient() as client:
            await self.single_time_init(client)
            id = self.getId(question, deployment_id)
            body = dict(
                id=id,
                question=question,
                answer=answer,
                success=success,
                score=score,
                deployment_id=deployment_id,
                embeddings=(await embedder.embed(question)).tolist()
            )
            try:
                await client.create(index=ES_INDEX, id=id, body=body)
            except elasticsearch.ConflictError:
                await client.update(index=ES_INDEX, id=id, body={'doc': body})
            return self.toQa(body)

    async def getQuestion(self, *, question: str=None, id: str=None, deployment_id: str=None) -> Optional[QA]:
        assert question or id
        if not id:
            id = self.getId(question, deployment_id)
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
    
    async def findRelated(self, question: str, own_id: str, deployment_id: str) -> List[QA]:
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
                                'term': {'deployment_id': deployment_id}
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
                            'term': {'deployment_id': deployment_id}
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

    async def getQuestions(self, deploymentId: str, page=1, sort=None, query=None) -> QAResult:
        async with ESClient() as client:
            await self.single_time_init(client)
            body = {
                'query': {
                    'bool': {
                        'must': [
                            {'match': {'deployment_id': deploymentId}}
                        ]   
                    }
                },
                'from': (page - 1) * self.PAGE_SIZE,
                'size': self.PAGE_SIZE,
                'track_total_hits': True
            }
            # Apply sort parameter if provided
            if query:
                body['query']['bool']['must'].append({
                    'multi_match': {
                        'query': query,
                        'fields': ['question^10', 'answer'],
                        'type': 'cross_fields',
                        'operator': 'and',
                    }
                })
            else:
                sort = sort or '-last_updated'
            if sort:
                order = "asc" if sort[0] == '+' else "desc"
                field = sort[1:]
                body["sort"] = [{field: {"order": order}}]
            body['fields'] = ['id', 'question', 'answer', 'success', 'score', 'deployment_id']
            ret = await BaseRetry(timeout=30)(client, 'search', index=ES_INDEX, body=body)
            total = ret['hits']['total']['value']
            results = []
            for hit in ret['hits']['hits']:
                data = hit['_source']
                data = dict(data)
                try:
                    results.append(data)
                except Exception as e:
                    print('ERROR PARSING DATASET', e)
                    continue
            return QAResult(results, total, total // self.PAGE_SIZE + 1, page)
        return QAResult([], 0, 0, 0)

