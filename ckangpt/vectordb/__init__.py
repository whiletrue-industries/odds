def get_vector_db_class():
    from .chroma import ChromaVectorDB
    return ChromaVectorDB


def get_vector_db_instance(*args, **kwargs):
    return get_vector_db_class()(*args, **kwargs)
