import unittest
from unittest.mock import patch, AsyncMock
from app import create_app, db
from app.email_utils import send_bulk_emails
import asyncio
import json

class SanitizationBugTest(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_message_is_sanitized_end_to_end(self, mock_smtp_class):
        """
        Tests that the HTML message is correctly sanitized for XSS vulnerabilities
        by calling the core logic directly, bypassing the HTTP layer.
        """
        # asyncio.run() is used to execute the async test method from a sync test.
        asyncio.run(self.async_sanitization_test(mock_smtp_class))

    async def async_sanitization_test(self, mock_smtp_class):
        # Arrange
        mock_smtp_instance = AsyncMock()
        # This configures the mock SMTP class to return our async mock instance
        mock_smtp_class.return_value.__aenter__.return_value = mock_smtp_instance

        malicious_payload = '<script>alert("XSS");</script><p>This is a <strong>safe</strong> message.</p>'
        expected_sanitized_body = '&lt;script&gt;alert("XSS");&lt;/script&gt;<p>This is a <strong>safe</strong> message.</p>'

        # Act
        # Call the function that contains the core logic directly
        await send_bulk_emails(
            subject='Test Subject',
            message=malicious_payload,
            manual_emails=['test@example.com'],
            base_url='http://testserver/',
            cc='',
            bcc='',
            attachments=[]
        )

        # Assert
        # 1. Check that the email sending function was actually called
        self.assertTrue(mock_smtp_instance.send_message.called)

        # 2. Extract the sent message from the mock
        sent_msg = mock_smtp_instance.send_message.call_args[0][0]

        # 3. Find and decode the HTML part of the email
        html_part = None
        if sent_msg.is_multipart():
            for part in sent_msg.walk():
                if part.get_content_type() == 'text/html':
                    html_part = part.get_payload(decode=True).decode('utf-8')
                    break

        self.assertIsNotNone(html_part, "HTML part of the email not found.")

        # 4. Assert that the sanitization worked as expected
        self.assertIn(expected_sanitized_body, html_part)
        self.assertNotIn('<script>alert', html_part)

if __name__ == '__main__':
    unittest.main()
