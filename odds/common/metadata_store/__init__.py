from .metadata_store import MetadataStore
from ..select import select
from .fs.fs_metadata_store import FSMetadataStore
from .s3.s3_metadata_store import S3MetadataStore
from .es.es_metadata_store import ESMetadataStore

metadata_store: MetadataStore = select('MetadataStore', locals())()