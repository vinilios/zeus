import markdown
import bleach

bleach.sanitizer.ALLOWED_TAGS = [u'h1', u'h2', u'h3', u'a', u'abbr', u'acronym', u'b', u'blockquote', u'code', u'em', u'i', u'li', u'ol', u'strong', u'ul', u'p']
bleach.sanitizer.ALLOWED_ATTRIBUTES = {u'a': [u'href', u'title'], u'acronym': [u'title'], u'abbr': [u'title']}
bleach.sanitizer.ALLOWED_PROTOCOLS = [u'http', u'https']

def parse_markdown(text):
    md = markdown.Markdown(
        safe_mode='escape',
        output_format='html5',
        extensions=[])
    html = md.convert(text)
    result = bleach.clean(html, tags=bleach.sanitizer.ALLOWED_TAGS)
    return result
