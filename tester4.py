from odds.common.select import CONFIG
# CONFIG['LLMRunner'] = 'MistralLLMRunner'

from odds.common.metadata_store import metadata_store
from odds.backend.processor.meta_describer import MetaDescriber


DATASET_ID = 'Canada/b9f51ef4-4605-4ef2-8231-62a2edda1b54'

async def main():
    describer = MetaDescriber()
    dataset = await metadata_store.getDataset(DATASET_ID)
    dataset.better_title = None
    dataset.better_description = None
    print(f'DESCRIBING {dataset.id}:\nTITLE: {dataset.title}\nDESCRIPTION: {dataset.description}')
    await describer.describe(dataset, 'test')
    print('-----------')
    print(f'RESULT\nB_TITLE: {dataset.better_title}\nB_DESCRIPTION: {dataset.better_description}')

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())