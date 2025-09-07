import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app import create_app
import base64
import asyncio
import aiosmtplib

from app.models import db

class EmailTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_send_email_task_success(self, mock_smtp):
        """
        Tests that the send_email_task function sends an email successfully.
        """
        # Mock the async context manager
        mock_smtp_context = AsyncMock()
        mock_smtp_context.starttls = AsyncMock()
        mock_smtp_context.login = AsyncMock()
        mock_smtp_context.send_message = AsyncMock()

        mock_smtp_instance = mock_smtp.return_value
        mock_smtp_instance.__aenter__.return_value = mock_smtp_context

        # Prepare the email data
        email_data = (
            ['test@example.com'],
            'Test Subject',
            '',
            '',
            'This is a test message.',
            [],
            'test-email-id'
        )
        base_url = 'http://localhost/'

        # Run the task
        from app.email_utils import send_email_task
        import asyncio
        result = asyncio.run(send_email_task(email_data, base_url))

        # Assertions
        self.assertEqual(result['status'], 'success')
        mock_smtp_context.send_message.assert_called_once()

    def test_attachment_validation_invalid_mime_type(self):
        """
        Tests that the attachment validation rejects files with invalid MIME types.
        """
        # Prepare a fake attachment with an invalid MIME type
        invalid_attachment = {
            'name': 'test.txt',
            'data': base64.b64encode(b'This is a test file.').decode('utf-8')
        }

        # Prepare the email data
        email_data = (
            ['test@example.com'],
            'Test Subject',
            '',
            '',
            'This is a test message.',
            [invalid_attachment],
            'test-email-id'
        )
        base_url = 'http://localhost/'

        # Run the task
        from app.email_utils import send_email_task
        import asyncio
        result = asyncio.run(send_email_task(email_data, base_url))

        # Assertions
        self.assertEqual(result['status'], 'error')
        self.assertIn('Tipo de anexo não permitido', result['message'])

    def test_save_and_get_template(self):
        """
        Tests that a template can be saved and then retrieved.
        """
        # Save a new template
        template_data = {
            'name': 'Test Template',
            'content': '<p>This is a test template.</p>'
        }
        response = self.client.post('/templates',
                                    data=json.dumps(template_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Get all templates
        response = self.client.get('/templates')
        self.assertEqual(response.status_code, 200)
        templates = json.loads(response.data)
        self.assertIn(template_data['name'], [t['name'] for t in templates])

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_check_smtp_credentials_auth_error(self, mock_smtp):
        async def run_test():
            mock_smtp_instance = mock_smtp.return_value
            mock_smtp_instance.connect = AsyncMock()
            mock_smtp_instance.starttls = AsyncMock()
            mock_smtp_instance.login.side_effect = aiosmtplib.SMTPAuthenticationError(1, "Auth error")

            from app.email_utils import check_smtp_credentials
            self.assertFalse(await check_smtp_credentials())
        asyncio.run(run_test())

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_check_smtp_credentials_other_error(self, mock_smtp):
        async def run_test():
            mock_smtp_instance = mock_smtp.return_value
            mock_smtp_instance.connect.side_effect = Exception("Connection failed")

            from app.email_utils import check_smtp_credentials
            self.assertFalse(await check_smtp_credentials())
        asyncio.run(run_test())

    def test_send_email_task_no_recipients(self):
        async def run_test():
            from app.email_utils import send_email_task
            email_data = ([], 'Subject', '', '', 'Message', [], 'email-id')
            result = await send_email_task(email_data, 'http://localhost/')
            self.assertEqual(result['status'], 'error')
        asyncio.run(run_test())

    @patch('app.socketio.emit')
    @patch('app.email_utils.send_email_task', new_callable=AsyncMock)
    def test_send_bulk_emails(self, mock_send_email_task, mock_socketio_emit):
        async def run_test():
            mock_send_email_task.return_value = {'status': 'success'}

            from app.email_utils import send_bulk_emails
            csv_content = "test1@example.com\ninvalid-email\ntest2@example.com"
            manual_emails = ["test3@example.com", "test1@example.com"]

            with self.app.app_context():
                result = await send_bulk_emails(
                    subject='Bulk Subject',
                    cc='', bcc='',
                    message='Bulk Message',
                    attachments=[],
                    base_url='http://localhost/',
                    csv_content=csv_content,
                    manual_emails=manual_emails
                )

            self.assertEqual(result['status'], 'success')
            self.assertEqual(mock_send_email_task.call_count, 3)
            self.assertEqual(mock_socketio_emit.call_count, 3)
        asyncio.run(run_test())

    @patch('app.email_utils.send_email_task', new_callable=AsyncMock)
    def test_send_bulk_emails_task_failure(self, mock_send_email_task):
        async def run_test():
            mock_send_email_task.return_value = {'status': 'error', 'message': 'Failed to send'}

            from app.email_utils import send_bulk_emails
            with self.app.app_context():
                result = await send_bulk_emails(
                    subject='Bulk Subject',
                    cc='', bcc='',
                    message='Bulk Message',
                    attachments=[],
                    base_url='http://localhost/',
                    manual_emails=['test@example.com']
                )

            self.assertEqual(result['status'], 'error')
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
