import typing

import fastapi

from ckangpt.frontend import find_datasets


router = fastapi.APIRouter()


@router.post('')
async def find_datasets_(
        user_prompt: str,
        db_queries: str,
        document_ids: typing.List[str] = fastapi.Query(None),
        num_results: int = find_datasets.config.DEFAULT_NUM_RESULTS,
):
    _, answer = find_datasets.main(
        user_prompt, db_queries.split('\n'), document_ids=document_ids, num_results=num_results
    )
    return answer
