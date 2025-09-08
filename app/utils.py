import bleach
from bleach.css_sanitizer import CSSSanitizer
from urllib.parse import urlparse, urljoin
from flask import request


def is_safe_url(target):
    """
    Checks if a URL is safe for redirection. A URL is considered safe if it is
    a relative URL or if its network location is the same as the application's.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


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

    allowed_protocols = list(bleach.sanitizer.ALLOWED_PROTOCOLS) + ['cid']

    # Allow color and font-weight properties in style attributes
    css_sanitizer = CSSSanitizer(allowed_css_properties=['color', 'font-weight'])

    sanitized_content = bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=False,  # Escapes disallowed tags instead of stripping them, which is safer.
        css_sanitizer=css_sanitizer
    )

    return sanitized_content
