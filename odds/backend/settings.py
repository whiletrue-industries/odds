DOCUMENT_FORMATS = ['pdf']
UNPROCESSABLE_DOCUMENT_FORMATS = [
    'doc', 'docx', 'pptx'
]
UNPROCESSABLE_OTHER_FORMATS = [
    'geojson', 'json', 'xml', 'shp', 'kml', 'geoxml'
]
UNPROCESSABLE_GOOD_FORMATS = UNPROCESSABLE_DOCUMENT_FORMATS + UNPROCESSABLE_OTHER_FORMATS
DOCUMENT_MIMETYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}
TABULAR_FORMATS = ['csv', 'xlsx', 'xls']
CONTENT_FORMATS = ['website'] + DOCUMENT_FORMATS
ALLOWED_FORMATS = TABULAR_FORMATS + CONTENT_FORMATS

