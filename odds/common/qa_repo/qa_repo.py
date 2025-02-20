import dataclasses
from typing import List, Optional
from ..datatypes import Dataset, Embedding

@dataclasses.dataclass
class QA:
    id: str
    question: str
    answer: str
    success: bool
    score: int
    deployment_id: str


class QARepo:

    async def storeQA(self, question: str, answer: str, success: bool, score: int, deployment_id: str) -> QA:
        return None

    async def getQuestion(self, *, question: str=None, id: str=None, deployment_id: str=None) -> Optional[QA]:
        return None
    
    async def findRelated(self, question: str, own_id: str, deployment_id: str=None) -> List[QA]:
        return []
        
