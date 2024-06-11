from odds.backend import backend
b = backend.ODDSBackend()
b.scan_specific(datasetId='uk/gp-prescribing-data')
del b
