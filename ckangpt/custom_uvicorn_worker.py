from uvicorn.workers import UvicornWorker


class CustomUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {"loop": "asyncio", "http": "auto"}
