from fastapi import APIRouter, Depends, HTTPException
from .resolve_firebase_user import FireBaseUser
from ..common.deployment_repo import deployment_repo
from ..common.catalog_repo import catalog_repo

router = APIRouter(
    prefix="/admin",
)

@router.get("/")
async def read_items(user: FireBaseUser):
    return dict(user=user)

@router.get("/deployments")
async def user_deployments(user: FireBaseUser):
    uid = user['uid']
    return await deployment_repo.deployments_for_user(uid)

@router.get("/deployment/{deployment_id}/catalogs")
async def deployment_catalogs(deployment_id: str, user: FireBaseUser):
    uid = user['uid']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if deployment.owner != uid:
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    catalogIds = deployment.catalogIds
    catalogs = [
        await catalog_repo.get_catalog(catalogId)
        for catalogId in catalogIds
    ]
    return catalogs

