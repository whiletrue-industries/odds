import typing

import fastapi

from ckangpt.frontend import get_potential_dataset_names


router = fastapi.APIRouter()


@router.post('')
async def get_potential_dataset_names_(
    claims: str,
):
    return get_potential_dataset_names.main(
        claims
    )
