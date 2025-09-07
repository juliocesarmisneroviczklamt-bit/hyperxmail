import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app import create_app
import base64

class EmailTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.client = self.app.test_client()

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_send_email_task_success(self, mock_smtp):
        """
        Tests that the send_email_task function sends an email successfully.
        """
        # Mock the SMTP client
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.connect = AsyncMock()
        mock_smtp_instance.starttls = AsyncMock()
        mock_smtp_instance.login = AsyncMock()
        mock_smtp_instance.send_message = AsyncMock()
        mock_smtp_instance.quit = AsyncMock()
        mock_smtp.return_value = mock_smtp_instance

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
        mock_smtp_instance.send_message.assert_called_once()

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

if __name__ == '__main__':
    unittest.main()
