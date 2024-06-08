from .store import Store
from ..select import select
from .fs.fs_store import FSStore
from .s3.s3_store import S3Store

store: Store = select('Store', locals())()