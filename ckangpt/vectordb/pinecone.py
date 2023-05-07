from .base import BaseItem, BaseCollection, BaseVectorDB


class PineconeItem(BaseItem):
    pass


class PineconeCollection(BaseCollection):

    def __init__(self, *args, **kwargs):
        # Initialize the collection based on vector db specific args / kwargs
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        # return the collection name
        raise NotImplementedError

    def add(self, items):
        # add items to the collection
        raise NotImplementedError

    def delete(self):
        # delete the collection
        raise NotImplementedError

    def reindex(self):
        # reindex the collection
        raise NotImplementedError

    def get_existing_item_ids(self, item_ids):
        # return list of item ids that exist in the collection from the given list of item ids
        raise NotImplementedError

    def get_item_document(self, item_id):
        # return the document for the given item id
        raise NotImplementedError

    def iterate_item_documents(self, item_ids=None):
        # iterate over item documents, optionally only on the given list of item ids
        raise NotImplementedError

    def iterate_item_ids(self, offset=0, limit=1000):
        # iterate over all the item ids in the collection, optionally with an offset and limit
        raise NotImplementedError

    def iterate_query_items(self, embeddings, num_results=5, where=None):
        # iterate over items based on given embeddings query, optionally with a where clause
        # where should be a dict of key value pairs, matching specific values in the item metadata
        raise NotImplementedError


class PineconeVectorDB(BaseVectorDB):
    Item = PineconeItem

    def __init__(self):
        # vector db specific initialization, should not accept any arguments, all configuration should be done via config
        super().__init__()

    @staticmethod
    def get_default_collection_name():
        # return the default collection name, based on config
        raise NotImplementedError

    @staticmethod
    def get_vector_db_provider_name():
        # return the vector db provider name
        return "pinecone"

    def persist(self):
        # persist the vector db, implement only if applicable
        pass

    def get_datasets_collection(self, override_collection_name=None):
        # return the datasets collection, optionally with an override collection name, otherwise use default
        raise NotImplementedError

    def get_or_create_datasets_collection(self, override_collection_name=None):
        # return the datasets collection, create if not exists, optionally with an override collection name, otherwise use default
        raise NotImplementedError

    def create_datasets_collection(self, override_collection_name=None):
        # create the datasets collection and return it, optionally with an override collection name, otherwise use default
        raise NotImplementedError

    def list_collections(self):
        # iterator of all collection objects in the vector db
        raise NotImplementedError

    def delete_collection(self, name):
        # delete the collection with the given name
        raise NotImplementedError
