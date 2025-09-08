import bleach

def sanitize_html(html_content):
    """
    Sanitizes HTML content to prevent XSS attacks, allowing a safe subset of tags and attributes
    suitable for rich text emails.
    """
    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span',
        'img', 'a', 'code'
    ]
    allowed_attributes = {
        '*': ['style'], 'img': ['src', 'alt', 'title', 'width', 'height'],
        'a': ['href', 'target', 'title'], 'td': ['align'], 'th': ['align']
    }

    sanitized_content = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=False  # Escapes disallowed tags instead of stripping them, which is safer.
    )

    return sanitized_content
