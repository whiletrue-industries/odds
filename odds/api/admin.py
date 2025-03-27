import dataclasses
from fastapi import APIRouter, Depends, HTTPException
from .resolve_firebase_user import FireBaseUser
from ..common.deployment_repo import deployment_repo
from ..common.catalog_repo import catalog_repo
from ..common.metadata_store import metadata_store

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
        catalog_repo.get_catalog(catalogId)
        for catalogId in catalogIds
    ]
    return catalogs

@router.get("/deployment/{deployment_id}/catalog/{catalog_id}")
async def get_catalog(deployment_id: str, catalog_id: str, user: FireBaseUser):
    uid = user['uid']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if deployment.owner != uid:
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    if catalog_id not in deployment.catalogIds:
        raise HTTPException(status_code=404, detail="Catalog not found in this deployment")
    catalog = catalog_repo.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return catalog

@router.get("/deployment/{deployment_id}/catalog/{catalog_id}/datasets")
async def get_catalog_datasets(deployment_id: str, catalog_id: str, user: FireBaseUser, page: int = 1):
    uid = user['uid']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if deployment.owner != uid:
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    if catalog_id not in deployment.catalogIds:
        raise HTTPException(status_code=404, detail="Catalog not found in this deployment")
    catalog = catalog_repo.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    result = await metadata_store.getDatasets(catalog_id, page=1)
    simple_datasets = []
    for dataset in result.datasets:
        d = dataclasses.asdict(dataset)
        for r in d['resources']:
            r.pop('content', None)
            r.pop('chunks', None)
            r.pop('fields', None)
        d.pop('embedding', None)
        d.pop('resources', None)
        simple_datasets.append(d)
    ret = dict(
        page=result.page,
        total=result.total,
        pages=result.pages,
        datasets=simple_datasets
    )
    return ret