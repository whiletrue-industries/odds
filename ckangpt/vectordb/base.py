class BaseItem:

    def __init__(self, id, embeddings=None, metadata=None, document=None):
        self.id = id
        self.embeddings = embeddings
        self.metadata = metadata
        self.document = document


class BaseCollection:
    pass


class BaseVectorDB:
    pass
