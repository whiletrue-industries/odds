import typing

import fastapi

from ckangpt.frontend import break_claim_to_subclaims


router = fastapi.APIRouter()


@router.post('')
async def break_claim_to_subclaims_(
        claim: str,
):
    return break_claim_to_subclaims.main(
        claim
    )
