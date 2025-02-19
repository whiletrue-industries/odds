import datetime

from ..realtime_status import RealtimeStatus, Status

from .models import Status as StatusModel
from .base_model import db

class PeeweeRealtimeStatus(RealtimeStatus):

    def __init__(self) -> None:
        db.create_tables([StatusModel])

    def set(self, ctx: str, message: str, kind='info') -> None:
        params = dict(
            message=message[:254],
            kind=kind,
            updated=datetime.datetime.now()
        )
        StatusModel.insert(ctx=ctx, **params)\
            .on_conflict('update', update=params, conflict_target=(StatusModel.ctx,))\
            .execute()
        print(f'{ctx}:{message}')

    def clear(self, ctx: str) -> None:
        StatusModel.delete().where(StatusModel.ctx == ctx, StatusModel.kind!='error').execute()

    def clearAll(self) -> None:
        StatusModel.delete().execute()

    def get(self) -> list[Status]:
        return [
            Status(ctx=s.ctx, msg=s.message, kind=s.kind, created=s.created, updated=s.updated)
            for s in StatusModel.select().where(StatusModel.kind!='error').order_by(-StatusModel.updated, -StatusModel.kind, StatusModel.ctx)
        ]

    def errors(self) -> list[Status]:
        return [
            Status(ctx=s.ctx, msg=s.message, kind=s.kind, created=s.created, updated=s.updated)
            for s in StatusModel.select().where(StatusModel.kind=='error').order_by(StatusModel.created)
        ]
