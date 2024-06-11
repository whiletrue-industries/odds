import sys
from odds.backend import backend
b = backend.ODDSBackend()
b.scan_specific(catalogId=sys.argv[1], datasetId=sys.argv[2])
del b
