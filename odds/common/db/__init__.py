from .db import DBStorage
from ..select import select
from .peewee.peewee_db import PeeweeDBStorage

db: DBStorage = select('DBStorage', locals())()