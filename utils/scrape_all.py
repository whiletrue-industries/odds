from odds.backend import backend
import sys

b = backend.ODDSBackend()

if len(sys.argv) > 1:
    selected_catalog = sys.argv[1]
    b.scan_specific(catalogId=selected_catalog)
else:
    b.scan_required()
del b
