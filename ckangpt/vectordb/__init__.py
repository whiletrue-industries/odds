from ckangpt import config


def get_vector_db_class():
    if config.USE_PINECONE:
        from .pinecone import PineconeVectorDB
        return PineconeVectorDB
    else:
        from .chroma import ChromaVectorDB
        return ChromaVectorDB


def get_vector_db_instance():
    return get_vector_db_class()()
