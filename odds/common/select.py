CONFIG = {
    'Config': 'YAMLConfig',
    'CatalogRepo': 'ConfigCatalogRepo',
    'Store': 'FSStore',
    'LLMRunner': 'MistralLLMRunner',
    'Embedder': 'OpenAIEmbedder',
    'Indexer': 'ChromaDBIndexer',
    'DBStorage': 'PeeweeDBStorage',
    'RealtimeStatus': 'PeeweeRealtimeStatus',
}

def select(kind, context):
    classname = CONFIG[kind]
    klass = context[classname]
    return klass