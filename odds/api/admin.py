import dataclasses
from fastapi import APIRouter, Depends, HTTPException
from .resolve_firebase_user import FireBaseUser
from ..common.deployment_repo import deployment_repo
from ..common.catalog_repo import catalog_repo
from ..common.metadata_store import metadata_store
from ..common.config import config

router = APIRouter(
    prefix="/admin",
)

@router.get("/")
async def read_items(user: FireBaseUser):
    return dict(user=user)

@router.get("/deployments")
async def user_deployments(user: FireBaseUser):
    if not user['superadmin']:
        email = user['email']
        return await deployment_repo.deployments_for_user(email)
    else:
        return await deployment_repo.load_deployments()

@router.get("/deployment/{deployment_id}/catalogs")
async def deployment_catalogs(deployment_id: str, user: FireBaseUser):
    email = user['email']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not (email in deployment.owners or user['superadmin']):
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    catalogIds = deployment.catalogIds
    catalogs = [
        catalog_repo.get_catalog(catalogId)
        for catalogId in catalogIds
    ]
    return catalogs

@router.get("/deployment/{deployment_id}/catalog/{catalog_id}")
async def get_catalog(deployment_id: str, catalog_id: str, user: FireBaseUser):
    email = user['email']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not (email in deployment.owners or user['superadmin']):
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    if catalog_id not in deployment.catalogIds:
        raise HTTPException(status_code=404, detail="Catalog not found in this deployment")
    catalog = catalog_repo.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return catalog

@router.get("/deployment/{deployment_id}/catalog/{catalog_id}/datasets")
async def get_catalog_datasets(deployment_id: str, catalog_id: str, user: FireBaseUser, page: int = 1, sort: str = None):
    email = user['email']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not (email in deployment.owners or user['superadmin']):
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    if catalog_id not in deployment.catalogIds:
        raise HTTPException(status_code=404, detail="Catalog not found in this deployment")
    catalog = catalog_repo.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    result = await metadata_store.getDatasets(catalog_id, page=page, sort=sort)
    simple_datasets = []
    for dataset in result.datasets:
        d = dataclasses.asdict(dataset)
        for r in d['resources']:
            r.pop('content', None)
            r.pop('chunks', None)
            r.pop('fields', None)
        d.pop('embedding', None)
        # d.pop('resources', None)
        simple_datasets.append(d)
    ret = dict(
        page=result.page,
        total=result.total,
        pages=result.pages,
        datasets=simple_datasets
    )
    return ret

@router.get("/deployment/{deployment_id}/catalog/{catalog_id}/dataset/{dataset_id}")
async def get_catalog_dataset(deployment_id: str, catalog_id: str, dataset_id: str, user: FireBaseUser):
    email = user['email']
    deployment = await deployment_repo.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not (email in deployment.owners or user['superadmin']):
        raise HTTPException(status_code=403, detail="Not authorized to access this deployment")
    if catalog_id not in deployment.catalogIds:
        raise HTTPException(status_code=404, detail="Catalog not found in this deployment")
    catalog = catalog_repo.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    store_id = f'{catalog_id}__{dataset_id}'
    dataset = await metadata_store.getDataset(store_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    d = dataclasses.asdict(dataset)
    for r in d['resources']:
        if r['content']:
            r['content-length'] = len(r['content'])
            r['content'] = r['content'][:300]
        r.pop('chunks', None)
        r.pop('fields', None)
    d.pop('embedding', None)
    return dataset