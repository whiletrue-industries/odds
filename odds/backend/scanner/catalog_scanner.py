from typing import AsyncIterator
from ...common.filters import Dataset, DatasetFilter


class CatalogScanner:

    async def scan(self) -> AsyncIterator[Dataset]:
        ...