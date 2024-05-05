import datetime
from .base_model import BaseModel
from peewee import TextField, CharField, DateTimeField


class Status(BaseModel):
    ctx = CharField(primary_key=True)
    message = TextField()
    kind = CharField()

    created = DateTimeField(default=datetime.datetime.now)
    

