from .store import Store
from ..select import select
from .fs.fs_store import FSStore

store: Store = select('Store', locals())()