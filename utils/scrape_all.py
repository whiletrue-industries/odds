import asyncio
import argparse

from arq import create_pool
from arq.connections import RedisSettings

REDIS_SETTINGS = RedisSettings('redis')

async def main():
    parser = argparse.ArgumentParser(description='Scrape data from all catalogs')
    parser.add_argument('--catalog-id', type=str, help='ID of the catalog to scrape')
    parser.add_argument('--dataset-id', type=str, help='ID of the dataset to scrape')
    parser.add_argument('--force', action='store_true', help='Scrape all and not just missing datasets')
    args = parser.parse_args()

    redis = await create_pool(REDIS_SETTINGS)
    catalog_id = args.catalog_id or None
    dataset_id = args.dataset_id or None
    print(f'SCAN SPECIFIC CATALOG: {catalog_id}, DATASET: {dataset_id}, FORCE? {args.force}')
    await redis.enqueue_job('scan_specific', catalog_id, dataset_id, args.force, _job_id='scraper_temp')

if __name__ == '__main__':
    asyncio.run(main())