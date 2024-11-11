import sys
from odds.common.embedder import embedder
from odds.common.vectordb import indexer
from odds.common.metadata_store import metadata_store

async def main():
    query = sys.argv[1]
    b = await embedder.embed(query)
    datasets = await indexer.findDatasets(b, query=query)
    # datasets = [await metadata_store.getDataset(id) for id in ids]
    for dataset in datasets:
        print(f' - {dataset.id}: {dataset.better_title}')


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())