import datetime
from .base_model import BaseModel
from peewee import TextField, CharField, BooleanField, ForeignKeyField, IntegerField, DateTimeField
from playhouse.postgres_ext import BinaryJSONField


class Catalog(BaseModel):
    id = CharField(primary_key=True)
    kind = CharField()
    url = TextField()
    title = CharField()
    description = TextField(null=True)
    geo = CharField(null=True)
    http_headers = BinaryJSONField(null=True)

    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super().save(*args, **kwargs)


class Dataset(BaseModel):
    id = CharField(primary_key=True)
    catalogId = ForeignKeyField(Catalog, backref='datasets')
    title = TextField()
    description = TextField(null=True)
    publisher = TextField(null=True)
    publisher_description = TextField(null=True)
    status_embedding = BooleanField(default=False)
    status_indexing = BooleanField(default=False)
    better_title = TextField(null=True)
    better_description = TextField(null=True)
    versions = BinaryJSONField(null=True)

    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super().save(*args, **kwargs)


class Resource(BaseModel):
    url = TextField(primary_key=True)
    file_format = CharField()
    title = TextField(null=True)
    row_count = IntegerField(null=True)
    db_schema = TextField(null=True)
    status_selected = BooleanField(default=False)
    status_loaded = BooleanField(default=False)
    loading_error = TextField(null=True)
    dataset = ForeignKeyField(Dataset, backref='resources')

    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super().save(*args, **kwargs)



