CONFIG = {
    'Config': 'YAMLConfig',
    'CatalogRepo': 'ConfigCatalogRepo',
    'DeploymentRepo': 'ConfigDeploymentRepo',
    # 'Store': 'FSStore',
    'MetadataStore': 'ESMetadataStore',
    'Store': 'S3Store',
    'LLMRunner': 'OpenAILLMRunner',
    'Embedder': 'OpenAIEmbedder',
    'Indexer': 'ESIndexer',
    'DBStorage': 'PeeweeDBStorage',
    'RealtimeStatus': 'PeeweeRealtimeStatus',
    'QARepo': 'ESQARepo',
}

def select(kind, context):
    classname = CONFIG[kind]
    klass = context[classname]
    return klass