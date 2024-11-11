CONFIG = {
    'Config': 'YAMLConfig',
    'CatalogRepo': 'ConfigCatalogRepo',
    'Store': 'FSStore',
    'MetadataStore': 'ESMetadataStore',
    # 'Store': 'S3Store',
    'LLMRunner': 'MistralLLMRunner',
    'Embedder': 'OpenAIEmbedder',
    'Indexer': 'ESIndexer',
    'DBStorage': 'PeeweeDBStorage',
    'RealtimeStatus': 'PeeweeRealtimeStatus',
}

def select(kind, context):
    classname = CONFIG[kind]
    klass = context[classname]
    return klass