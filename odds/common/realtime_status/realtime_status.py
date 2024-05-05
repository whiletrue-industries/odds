from dataclasses import dataclass
import datetime

@dataclass
class Status:
    ctx: str
    msg: str
    kind: str
    created: datetime.datetime


class RealtimeStatus:

    def set(self, ctx: str, message: str, kind: str) -> None:
        pass

    def clear(self, ctx: str) -> None:
        pass

    def clearAll(self) -> None:
        pass

    def get(self) -> list[Status]:
        pass

    def errors(self) -> list[Status]:
        pass

