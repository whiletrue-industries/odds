import asyncio
from typing import Coroutine, Any
from httpx import Response


class Retry:

    def __init__(self, retries=3) -> None:
        self.retries = retries

    # operation is an async function that returns a httpx.Response
    async def __call__(self, client, method, *args, **kwargs) -> Response:
        response = None
        for i in range(self.retries):
            try:
                response = None
                response = await getattr(client, method)(*args, **kwargs)
                if response.status_code == 400:
                    print('ERROR', response.status_code, response.text)
                    return None
                response.raise_for_status()
                return response
            except Exception as e:
                if response:
                    print('RETRYING', repr(e), args[0], response.status_code, response.text)
                else:
                    print('RETRYING', repr(e), args[0])
                if i == self.retries - 1:
                    print('GIVING UP', repr(e), args[0])
                await asyncio.sleep(2 ** (i+2))
        return None
        