import unittest
from unittest.mock import patch, AsyncMock
from app import create_app, db
from app.email_utils import send_bulk_emails
import asyncio
import json
import os

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

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_html_in_attribute_is_escaped(self, mock_smtp_class):
        """
        Tests that HTML inside an attribute (like 'title') is properly escaped.
        """
        asyncio.run(self.async_html_in_attribute_test(mock_smtp_class))

    async def async_html_in_attribute_test(self, mock_smtp_class):
        # Arrange
        mock_smtp_instance = AsyncMock()
        mock_smtp_class.return_value.__aenter__.return_value = mock_smtp_instance

        malicious_payload = '<a href="http://example.com" title="<img src=x onerror=alert(1)>">Click me</a>'

        # Act
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
        sent_msg = mock_smtp_instance.send_message.call_args[0][0]
        html_part = None
        if sent_msg.is_multipart():
            for part in sent_msg.walk():
                if part.get_content_type() == 'text/html':
                    html_part = part.get_payload(decode=True).decode('utf-8')
                    break

        self.assertIsNotNone(html_part, "HTML part of the email not found.")
        self.assertNotIn("onerror", html_part)
        self.assertIn('title=""', html_part)


if __name__ == '__main__':
    unittest.main()


class TemplateSavingBugTest(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        # Define a path for a temporary templates file and ensure it's clean
        self.templates_file_path = self.app.config['TEMPLATES_FILE_PATH']
        if os.path.exists(self.templates_file_path):
            os.remove(self.templates_file_path)

    def tearDown(self):
        # Clean up the temporary templates file
        if os.path.exists(self.templates_file_path):
            os.remove(self.templates_file_path)
        self.app_context.pop()

    def test_saving_template_strips_html_tags(self):
        """
        Confirms the bug: saving a template incorrectly strips out all HTML tags.
        This test will initially pass (confirming the bug), then be modified to
        fail, and finally pass again once the bug is fixed.
        """
        # Arrange: The HTML content to be saved
        template_name = "My Test Template"
        html_content = "<p>Hello, <strong>World!</strong></p>"

        # This is what the buggy code produces
        # expected_content_with_bug = "Hello, World!"

        # This is what the code SHOULD produce
        expected_content_fixed = "<p>Hello, <strong>World!</strong></p>"

        # Act: Post the new template to the /templates endpoint
        response = self.client.post('/templates',
                                     data=json.dumps({'name': template_name, 'content': html_content}),
                                     content_type='application/json')

        # Assert: Check the response and the file content
        self.assertEqual(response.status_code, 201)

        # Verify the content of the saved file
        with open(self.templates_file_path, 'r') as f:
            templates = json.load(f)

        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['name'], template_name)

        # This is the assertion that SHOULD pass after the fix.
        self.assertEqual(templates[0]['content'], expected_content_fixed)
