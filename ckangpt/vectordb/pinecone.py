import json

import pinecone

from .base import BaseItem, BaseCollection, BaseVectorDB
from ckangpt import config


class PineconeItem(BaseItem):
    pass


class PineconeCollection(BaseCollection):

    def __init__(self, index_name):
        self._index_name = index_name

    @property
    def name(self):
        return self._index_name

    def add(self, items):
        pinecone.Index(self._index_name).upsert([
            (item.id, item.embeddings, {'document': item.document, **item.metadata})
            for item in items
        ])

    def reindex(self):
        raise Exception("Pinecone does not support reindexing")

    def get_existing_item_ids(self, item_ids):
        return list(pinecone.Index(self._index_name).fetch(item_ids)['vectors'].keys()) if item_ids else []

    def get_item_document(self, item_id):
        return pinecone.Index(self._index_name).fetch([item_id])['vectors'][item_id]['metadata']['document']

    def iterate_item_documents(self, item_ids=None):
        assert item_ids, 'Pinecone does not support iterating over all item documents'
        for item_id, res in pinecone.Index(self._index_name).fetch(item_ids)['vectors'].items():
            yield item_id, res['metadata']['document']

    def iterate_item_ids(self, offset=0, limit=1000):
        # iterate over all the item ids in the collection, optionally with an offset and limit
        assert offset == 0, "Pinecone does not support offset"
        print("WARNING! Pinecone does not support iterating over all items, returning partial list")
        res = pinecone.Index(self._index_name).query(vector=[0 for _ in range(1536)], top_k=limit)
        for match in res['matches']:
            yield match['id']

    def iterate_query_items(self, embeddings, num_results=5, where=None):
        for match in pinecone.Index(self._index_name).query(vector=embeddings, top_k=num_results, filter=where, include_metadata=True)['matches']:
            metadata = match['metadata']
            document = metadata.pop('document')
            yield PineconeItem(
                id=match['id'],
                metadata=metadata,
                document=document,
            )


class PineconeVectorDB(BaseVectorDB):
    Item = PineconeItem

    def __init__(self):
        # vector db specific initialization, should not accept any arguments, all configuration should be done via config
        pinecone.init(api_key=config.PINECONE_API_KEY, environment=config.PINECONE_ENVIRONMENT)

    @staticmethod
    def get_default_collection_name():
        return config.PINECONE_DATASETS_COLLECTION_NAME

    @staticmethod
    def get_vector_db_provider_name():
        # return the vector db provider name
        return "pinecone"

    def persist(self):
        # persist the vector db, implement only if applicable
        pass

    def get_datasets_collection(self, override_collection_name=None):
        index_name = override_collection_name or self.get_default_collection_name()
        return PineconeCollection(index_name)

    def create_datasets_collection(self, override_collection_name=None):
        index_name = override_collection_name or self.get_default_collection_name()
        print(f"Creating Pinecone index {index_name}, this may take a few minutes...")
        # 1536 is the embeddings length returned by OpenAI's embedding API
        from ..vectordb import get_indexed_metadata_fields
        pinecone.create_index(index_name, 1536, metadata_config={
            "indexed": get_indexed_metadata_fields()
        })
        return PineconeCollection(index_name)

    def list_collections(self):
        # iterator of all collection objects in the vector db
        for index_name in pinecone.list_indexes():
            yield PineconeCollection(index_name)

    def delete_collection(self, name):
        pinecone.delete_index(name)
