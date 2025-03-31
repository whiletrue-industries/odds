from markdownify import markdownify as md

def html_to_markdown(text):
    if text and ('<br' in text or '<b' in text or '<a' in text):
        return md(text)
    return text 
