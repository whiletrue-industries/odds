from odds.backend import backend
import sys
import argparse

parser = argparse.ArgumentParser(description='Scrape data from all catalogs')
parser.add_argument('--catalog-id', type=str, help='ID of the catalog to scrape')
parser.add_argument('--force', type=bool, default=False, help='Scrape all and not just missing datasets')
args = parser.parse_args()

b = backend.ODDSBackend()
b.scan_specific(catalogId=args.catalog_id, force=args.force)
del b
