from .realtime_status import RealtimeStatus
from ..select import select
from .peewee.peewee_rts import PeeweeRealtimeStatus

realtime_status: RealtimeStatus = select('RealtimeStatus', locals())()