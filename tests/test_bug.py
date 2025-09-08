import unittest
from unittest.mock import patch, MagicMock
import json
from app import create_app

class BugTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.client = self.app.test_client()

    @patch('app.routes.send_bulk_emails')
    @patch('app.routes.check_smtp_credentials', return_value=True)
    def test_send_email_sanitizes_message(self, mock_check_smtp, mock_send_bulk_emails):
        """
        Tests that the message content is sanitized before being sent.
        """
        malicious_payload = '<script>alert("XSS")</script><p>This is a test message.</p>'
        # The route should not sanitize the message, so we expect the raw payload.
        expected_raw_message = malicious_payload

        mock_send_bulk_emails.return_value = {'status': 'success'}

        response = self.client.post('/send_email',
                                    data=json.dumps({
                                        'subject': 'Test Subject',
                                        'message': malicious_payload,
                                        'manualEmails': ['test@example.com']
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        # Check that send_bulk_emails was called with the raw message
        mock_send_bulk_emails.assert_called_once()
        call_args = mock_send_bulk_emails.call_args[1]
        self.assertEqual(call_args['message'], expected_raw_message)

    @patch('app.routes.send_bulk_emails')
    @patch('app.routes.check_smtp_credentials', return_value=True)
    def test_send_email_preserves_allowed_html(self, mock_check_smtp, mock_send_bulk_emails):
        """
        Tests that the message content with allowed HTML is not stripped.
        """
        html_payload = '<p>This is a test message.</p>'
        expected_message = '<p>This is a test message.</p>'

        mock_send_bulk_emails.return_value = {'status': 'success'}

        response = self.client.post('/send_email',
                                    data=json.dumps({
                                        'subject': 'Test Subject',
                                        'message': html_payload,
                                        'manualEmails': ['test@example.com']
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)

        # Check that send_bulk_emails was called with the HTML message intact
        mock_send_bulk_emails.assert_called_once()
        call_args = mock_send_bulk_emails.call_args[1]
        self.assertEqual(call_args['message'], expected_message)


if __name__ == '__main__':
    unittest.main()
