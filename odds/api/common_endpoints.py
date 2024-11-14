from typing import Any
from odds.common.vectordb import indexer
from odds.common.store import store
from odds.common.metadata_store import metadata_store
from odds.common.embedder import embedder
from odds.common.catalog_repo import catalog_repo
import sqlite3

import logging


def encode_id(id):
    return id.replace('/', ':')

def decode_id(id):
    return id.replace(':', '/')

def parse_resource_id(id):
    id = decode_id(id)
    parts = id.split('/')
    datasetId = '/'.join(parts[:-1])
    resourceIdx = parts[-1]
    resourceIdx = int(resourceIdx)
    return datasetId, resourceIdx


async def search_datasets(query: str, catalog_id: str | None) -> list[dict[str, Any]]:
    logging.debug(f'SEARCH DATASETS: {query}')
    embedding = await embedder.embed(query)
    datasets = await indexer.findDatasets(embedding, query, catalog_id=catalog_id)
    catalogs = [catalog_repo.get_catalog(dataset.catalogId) for dataset in datasets]
    logging.debug(f'CATALOGS: {[catalog.title for catalog in catalogs]}')
    response = [
        dict(
            id=encode_id(dataset.storeId()),
            title=dataset.better_title or dataset.title,
            description=dataset.better_description or dataset.description,
            publisher=dataset.publisher,
            catalog=catalog.title,
            link=dataset.link,
        )
        for dataset, catalog in zip(datasets, catalogs)
    ]
    logging.debug(f'RESPONSE: {response}')
    return response

async def fetch_dataset(id):
    logging.debug(f'FETCH DATASET: {id}')
    id = decode_id(id)
    dataset = await metadata_store.getDataset(id)
    response = None
    if dataset:
        response = dict(
            title=dataset.better_title or dataset.title,
            description=dataset.better_description or dataset.description,
            publisher=dataset.publisher,
            publisher_description=dataset.publisher_description,
            link=dataset.link,
            resources=[]
        )
        for i, resource in enumerate(dataset.resources):
            to_add = dict()
            if resource.row_count:
                to_add.update(
                    dict(
                        id=encode_id(f'{id}/{i}'),
                        name=resource.title,
                        num_rows=resource.row_count,
                    )
                )
            if resource.content:
                to_add.update(
                    dict(
                        content=resource.content,
                        db_schema='no db schema available'
                    )
                )
            if to_add:
                response['resources'].append(to_add)

    logging.debug('RESPONSE:', response)
    return response

async def fetch_resource(id):
    logging.debug('FETCH RESOURCE:', id)
    datasetId, resourceIdx = parse_resource_id(id)
    dataset = await metadata_store.getDataset(datasetId)
    response = None
    if dataset:
        resource = dataset.resources[resourceIdx]
        if resource:
            response = dict(
                name=resource.title,
                fields=[
                    dict(
                        (k,v)
                        for k,v in dict(
                            name=field.name,
                            title=field.title,
                            description=field.description,
                            type=field.data_type,
                            max=field.max_value,
                            min=field.min_value,
                            sample_values=field.sample_values,
                        ).items()
                        if v is not None
                    )
                    for field in resource.fields
                ],
                db_schema=resource.db_schema
            )
        logging.debug(f'RESPONSE: {response}')
    return response

async def query_db(resource_id, sql):
    logging.debug(f'QUERY DB: {resource_id} -> {sql}')
    datasetId, resourceIdx = parse_resource_id(resource_id)
    dataset = await metadata_store.getDataset(datasetId)
    if dataset:
        resource = dataset.resources[resourceIdx]
        if resource:
            dbFile = await store.getDB(resource, dataset)
            if dbFile is None:
                logging.debug(f'FAILED TO FIND DB FOR {resource.title}')
                return None
            try:
                # TODO - move to async
                con = sqlite3.connect(dbFile)
                cur = con.cursor()
                cur.execute(sql)
                # Fetch data as a list of dicts:
                data = cur.fetchall()
                headers = [x[0] for x in cur.description]
                data = [dict(zip(headers, row)) for row in data]
                data = data[:100]
                logging.debug(f'GOT {len(data)} ROWS')
                return dict(success=True, data=data)
            except Exception as e:
                logging.debug(f'FAILED TO QUERY DB: {dbFile}, {e!r}')
                return dict(success=False, error=str(e))
    return None
