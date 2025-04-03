import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class QA:
    id: str
    question: str
    answer: str
    success: bool
    score: int
    deployment_id: str
    last_updated: str = None


@dataclasses.dataclass
class QAResult:
    questions: List[QA]
    total: int
    pages: int
    page: int


class QARepo:

    async def storeQA(self, question: str, answer: str, success: bool, score: int, deployment_id: str) -> QA:
        return None

    async def getQuestion(self, *, question: str=None, id: str=None, deployment_id: str=None) -> Optional[QA]:
        return None
    
    async def findRelated(self, question: str, own_id: str, deployment_id: str=None) -> List[QA]:
        return []
        
    async def getQuestions(self, deploymentId: str, page=1, sort=None, query=None) -> QAResult:
        return QAResult([], 0, 0, page)