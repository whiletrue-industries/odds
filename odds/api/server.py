import asyncio
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional

from collections import Counter
from odds.common.vectordb import indexer
from odds.common.store import store
from odds.common.embedder import embedder
from odds.common.catalog_repo import catalog_repo
import sqlite3

import asyncio

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


async def search_datasets(query: str):
    logging.debug(f'SEARCH DATASETS: {query}')
    query_terms = query.split(',')
    query_terms = [term.strip() for term in query_terms]
    query_terms = [term for term in query_terms if term]
    logging.debug(f'QUERY TERMS: {query_terms}')
    embeddings = await asyncio.gather(*[embedder.embed(name) for name in query_terms])
    dataset_ids = await asyncio.gather(*[indexer.findDatasets(embedding) for embedding in embeddings])
    dataset_ids = [x for y in dataset_ids for x in y]
    dataset_ids = [x[0] for x in Counter(dataset_ids).most_common(10)]
    logging.debug(f'DATASET IDS: {dataset_ids}')
    datasets = await asyncio.gather(*[store.getDataset(id) for id in dataset_ids])
    catalogs = [catalog_repo.get_catalog(dataset.catalogId) for dataset in datasets]
    logging.debug(f'CATALOGS: {[catalog.title for catalog in catalogs]}')
    response = [
        dict(
            id=encode_id(dataset.storeId()),
            title=dataset.better_title or dataset.title,
            description=dataset.better_description or dataset.description,
            publisher=dataset.publisher,
            catalog=catalog.title,
        )
        for dataset, catalog in zip(datasets, catalogs)
    ]
    logging.debug(f'RESPONSE: {response}')
    return response

async def fetch_dataset(id):
    logging.debug(f'FETCH DATASET: {id}')
    id = decode_id(id)
    dataset = await store.getDataset(id)
    response = None
    if dataset:
        response = dict(
            title=dataset.better_title or dataset.title,
            description=dataset.better_description or dataset.description,
            publisher=dataset.publisher,
            publisher_description=dataset.publisher_description,
            resources=[
                dict(
                    id=encode_id(f'{id}/{i}'),
                    name=resource.title,
                    num_rows=resource.row_count,
                )
                for i, resource in enumerate(dataset.resources)
                if resource.row_count
            ],            
        )
    logging.debug('RESPONSE:', response)
    return response

async def fetch_resource(id):
    logging.debug('FETCH RESOURCE:', id)
    datasetId, resourceIdx = parse_resource_id(id)
    dataset = await store.getDataset(datasetId)
    response = None
    if dataset:
        resource = dataset.resources[resourceIdx]
        if resource:
            response = dict(
                name=resource.title,
                fields=[
                    dict(
                        name=field.name,
                        type=field.data_type,
                        max=field.max_value,
                        min=field.min_value,
                        sample_values=field.sample_values,
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
    dataset = await store.getDataset(datasetId)
    if dataset:
        resource = dataset.resources[resourceIdx]
        if resource:
            dbFile = await store.getDB(resource, dataset)
            if dbFile is None:
                logging.debug(f'FAILED TO FIND DB FOR {resource.title}')
                return None
            try:
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


### A FastAPI server that serves the odds API
# Exposes the following methods:
# - search_datasets(query: str) -> List[Dict[str, str]]
# - fetch_dataset(id: str) -> Optional[Dict[str, str]]
# - fetch_resource(id: str) -> Optional[Dict[str, str]]
# - query_db(resource_id: str, query: str) -> Optional[Dict[str, Any]]

app = FastAPI()

@app.get("/datasets")
async def search_datasets_handler(query: str) -> List[Dict[str, str]]:
    return await search_datasets(query)

@app.get("/dataset/{id}")
async def fetch_dataset_handler(id: str) -> Optional[Dict[str, Any]]:
    return await fetch_dataset(id)

@app.get("/resource/{id}")
async def fetch_resource_handler(id: str) -> Optional[Dict[str, Any]]:
    return await fetch_resource(id)

@app.get("/query/{resource_id}")
async def query_db_handler(resource_id: str, sql: str) -> Optional[Dict[str, Any]]:
    return await query_db(resource_id, sql)

# Run the server with:
# uvicorn server:app --reload
