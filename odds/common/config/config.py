from typing import Any

class _Getter:

    def __init__(self, data: Any):
        self.data = data

    def get(self, key):
        return self.data.get(key)
    
    def __getattr__(self, __name: str) -> Any:
        ret = self.get(__name)
        if isinstance(ret, dict):
            return _Getter(ret)
        return ret


class Config(_Getter):
    ...