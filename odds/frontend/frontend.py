import asyncio
from collections import Counter
import sqlite3

from slugify import slugify
from .steps import *
from ..common.vectordb import indexer
from ..common.store import store
from ..common.embedder import embedder
from ..common.datatypes import Dataset, Resource
from ..common.catalog_repo import catalog_repo

class ODDSFrontend:

    async def analyze_text(self, text: str) -> str:
        conversation = ['text']
        claims = await extract_claims(text, conversation=conversation)
        verdicts = await asyncio.gather(*[self.verify_claim(claim, conversation=conversation) for claim in claims[:1]])
        return verdicts
        # conclusion = await compose_conclusion(text, zip(claims, verdicts))
        # return conclusion

    async def verify_claim(self, claim: str, conversation: list[str]=[]) -> str:
        conversation = conversation + [claim] #[slugify(claim, separator='_')[:64]]
        subclaims = await simplify_claim(claim, conversation=conversation)
        verdicts = await asyncio.gather(*[self.verify_subclaim(subclaim, conversation=conversation) for subclaim in subclaims])
        return verdicts
        # return await compose_claim_verdict(claim, subclaims, verdicts)

    async def verify_subclaim(self, subclaim: str, conversation: list[str]=[]) -> str:
        conversation = conversation + [subclaim] # [slugify(subclaim, separator='_')[:64]]
        datapoints = await extract_datapoints(subclaim, conversation=conversation)
        statements = await asyncio.gather(*[self.fetch_data(datapoint, conversation=conversation) for datapoint in datapoints])
        return await compose_subclaim_verdict(subclaim, statements)
    
    async def fetch_data(self, datapoint: str, conversation: list[str]=[]) -> str:
        conversation = conversation + [datapoint] # [slugify(datapoint, separator='_')[:64]]
        possible_dataset_names = await guess_dataset_names(datapoint, conversation=conversation)
        embeddings = await asyncio.gather(*[embedder.embed(name) for name in possible_dataset_names])
        dataset_ids = await asyncio.gather(*[indexer.findDatasets(embedding) for embedding in embeddings])
        # flatten dataset_ids:
        dataset_ids = [x for y in dataset_ids for x in y]
        dataset_ids = [x[0] for x in Counter(dataset_ids).most_common(10)]
        datasets = await asyncio.gather(*[store.getDataset(id) for id in dataset_ids])
        catalogs = [catalog_repo.get_catalog(dataset.catalogId) for dataset in datasets]
        dataset_id = await select_best_dataset(datapoint, datasets, catalogs, conversation=conversation)
        data = None
        data_explanation = None
        if dataset_id is not None:
            dataset = await store.getDataset(dataset_id)
            if dataset is not None:
                if len(dataset.resources) > 0:
                    if len(dataset.resources) == 1:
                        resource = dataset.resources[0]
                    else:
                        resource = await select_best_resource(datapoint, dataset, conversation=conversation)
                    if resource is not None:
                        query, explanation = await compose_query(datapoint, resource, dataset, conversation=conversation)
                        if query is not None:
                            data = await self.query_db(dataset, resource, query)
                            data_explanation = explanation
                            assert data is not None
        statement = await convert_to_statement(datapoint, data, data_explanation, conversation=conversation)
        return statement
        

    async def query_db(self, dataset: Dataset, resource: Resource, query: str) -> str:
        dbFile = await store.getDB(resource, dataset)
        if dbFile is None:
            print('FAILED TO FIND DB', dbFile)
            return None
        try:
            con = sqlite3.connect(dbFile)
            cur = con.cursor()
            cur.execute(query)
            # Fetch data as a list of dicts:
            data = cur.fetchall()
            headers = [x[0] for x in cur.description]
            data = [dict(zip(headers, row)) for row in data]
            print('GOT DATA', data)
            return data
        except Exception as e:
            print('FAILED TO QUERY DB', dbFile, repr(e))

