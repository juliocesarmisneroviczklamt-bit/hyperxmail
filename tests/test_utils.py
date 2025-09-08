import unittest
from app.utils import sanitize_html
from app.email_utils import sanitize_filename


class UtilsTestCase(unittest.TestCase):
    def test_sanitize_html_removes_malicious_attributes(self):
        """
        Tests that sanitize_html removes dangerous attributes like 'onclick'.
        """
        malicious_html = (
            '<a href="http://example.com" onclick="alert(\'XSS\')">Click me</a>'
        )
        sanitized_html = sanitize_html(malicious_html)
        self.assertNotIn("onclick", sanitized_html)
        self.assertIn('href="http://example.com"', sanitized_html)

    def test_sanitize_html_preserves_allowed_tags(self):
        """
        Tests that sanitize_html keeps safe, allowed tags like <p> and <strong>.
        """
        safe_html = "<p>This is a <strong>safe</strong> message.</p>"
        sanitized_html = sanitize_html(safe_html)
        self.assertEqual(sanitized_html, safe_html)

    def test_sanitize_html_escapes_disallowed_tags(self):
        """
        Tests that sanitize_html escapes dangerous tags like <script>.
        """
        malicious_html = '<script>alert("XSS");</script><p>Safe part</p>'
        sanitized_html = sanitize_html(malicious_html)
        self.assertIn('&lt;script&gt;alert("XSS");&lt;/script&gt;', sanitized_html)
        self.assertIn("<p>Safe part</p>", sanitized_html)

    def test_sanitize_html_allows_img_and_cid_protocol(self):
        """
        Tests that <img> tags and the 'cid:' protocol for embedded images are allowed.
        """
        img_html = '<img src="cid:image123" alt="Embedded Image">'
        sanitized_html = sanitize_html(img_html)
        self.assertIn('<img src="cid:image123"', sanitized_html)
        self.assertIn('alt="Embedded Image"', sanitized_html)

    def test_sanitize_html_allows_style_attributes(self):
        """
        Tests that 'style' attributes are allowed on elements.
        """
        styled_html = '<p style="color:red; font-weight:bold;">Styled text</p>'
        sanitized_html = sanitize_html(styled_html)
        self.assertRegex(
            sanitized_html, r'style="color:\s*red;\s*font-weight:\s*bold;"'
        )

    def test_sanitize_filename_removes_dangerous_characters(self):
        """
        Tests that sanitize_filename removes characters that could be used for path traversal.
        """
        malicious_filename = "//etc/passwd"
        sanitized = sanitize_filename(malicious_filename)
        self.assertEqual(sanitized, "etcpasswd")

    def test_sanitize_filename_allows_safe_characters(self):
        """
        Tests that sanitize_filename preserves safe, standard characters.
        """
        safe_filename = "report_2024-03-15_final.pdf"
        sanitized = sanitize_filename(safe_filename)
        self.assertEqual(sanitized, safe_filename)

    def test_sanitize_filename_handles_special_characters(self):
        """
        Tests that sanitize_filename removes various special characters.
        """
        special_char_filename = "file@name#with$special%chars&.txt"
        sanitized = sanitize_filename(special_char_filename)
        self.assertEqual(sanitized, "filenamewithspecialchars.txt")


if __name__ == "__main__":
    unittest.main()
