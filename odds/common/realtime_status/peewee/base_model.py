from ...config import config
from peewee import Model
from playhouse.postgres_ext import PostgresqlExtDatabase

DATABASE_CONNECTION_STR = config.credentials.db_store.connection

db = PostgresqlExtDatabase(DATABASE_CONNECTION_STR, autorollback=True)

class BaseModel(Model):
    class Meta:
        database = db