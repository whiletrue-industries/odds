DOCUMENT_FORMATS = ['pdf']#, 'doc', 'docx', 'pptx']
DOCUMENT_MIMETYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}
ALLOWED_FORMATS = ['csv', 'xlsx', 'xls', 'website'] + DOCUMENT_FORMATS

