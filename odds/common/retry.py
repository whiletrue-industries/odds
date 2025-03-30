import asyncio
from typing import Coroutine, Any
from httpx import Response


class BaseRetry:

    def __init__(self, retries=3, timeout=2) -> None:
        self.retries = retries
        self.timeout = timeout

    # operation is an async function that returns a httpx.Response
    async def __call__(self, client, method, *args, **kwargs) -> Response:
        response = None
        for i in range(self.retries):
            try:
                response = None
                response = await getattr(client, method)(*args, **kwargs)
                response = self.test_response(response)
                return response
            except Exception as e:
                print('RETRYING', repr(e), repr(client), method, args, kwargs)
                if i == self.retries - 1:
                    print('GIVING UP', repr(e), repr(client), method, args, kwargs)
                await asyncio.sleep(self.timeout * (2 ** (i+2)))
        return None

    def test_response(self, response: Response) -> None:
        return response

class Retry(BaseRetry):

    def __init__(self, retries=3, timeout=2) -> None:
        super().__init__(retries=retries, timeout=timeout)

    def test_response(self, response: Response) -> None:
        if response.status_code == 400:
            print('ERROR', response.status_code, response.text)
            return None
        try:
            response.raise_for_status()
        except Exception as e:
            print('RETRYING', repr(e), response.url, response.status_code, response.text[:200])
            raise
        return response

        