import typing

import fastapi

from ckangpt.frontend import get_potential_dataset_names


router = fastapi.APIRouter()


@router.get('')
async def get_potential_dataset_names_(
    claims: typing.List[str],
):
    return get_potential_dataset_names.main(
        claims
    )
