from .qa_repo import QARepo
from ..select import select
from .es.es_qa_repo import ESQARepo

qa_repo: QARepo = select('QARepo', locals())()