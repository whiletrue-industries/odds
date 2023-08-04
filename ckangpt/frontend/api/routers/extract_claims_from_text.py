import typing

import fastapi

from ckangpt.frontend import extract_claims_from_text


router = fastapi.APIRouter()


@router.get('')
async def extract_claims_from_text_(
        text: str,
):
    return extract_claims_from_text.main(
        text
    )
