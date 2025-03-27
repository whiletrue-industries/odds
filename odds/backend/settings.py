DOCUMENT_FORMATS = ['pdf', 'doc', 'docx']
DOCUMENT_MIMETYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}
ALLOWED_FORMATS = ['csv', 'xlsx', 'xls', 'website'] + DOCUMENT_FORMATS

