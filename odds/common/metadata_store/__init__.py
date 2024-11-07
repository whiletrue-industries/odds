from .metadata_store import MetadataStore
from ..select import select
from .fs.fs_metadata_store import FSMetadataStore
from .s3.s3_metadata_store import S3MetadataStore

metadata_store: MetadataStore = select('MetadataStore', locals())()