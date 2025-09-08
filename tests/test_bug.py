import unittest
from unittest.mock import patch
import json
from app import create_app, db
from app.models import Campaign

class SanitizationTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('app.email_utils.send_email_task', return_value={'status': 'success'})
    @patch('app.routes.check_smtp_credentials', return_value=True)
    def test_message_is_sanitized_before_storage_and_sending(self, mock_check_smtp, mock_send_email_task):
        """
        Tests that the message is correctly sanitized before being stored in the database
        and passed to the email sending task.
        """
        malicious_payload = '<script>alert("XSS");</script><p>This is a <strong>safe</strong> message.</p>'
        # bleach.clean with strip=True removes the tag but leaves the content. This is expected.
        expected_sanitized_message = 'alert("XSS");<p>This is a <strong>safe</strong> message.</p>'

        # Action: Send a request to the /send_email endpoint
        response = self.client.post('/send_email',
                                    data=json.dumps({
                                        'subject': 'Test Subject',
                                        'message': malicious_payload,
                                        'manualEmails': ['test@example.com']
                                    }),
                                    content_type='application/json')

        # Assertion 1: Check the HTTP response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')

        # Assertion 2: Check the content stored in the database
        with self.app.app_context():
            campaign = Campaign.query.first()
            self.assertIsNotNone(campaign)
            self.assertEqual(campaign.message, expected_sanitized_message)

        # Assertion 3: Check that the email task was called with the sanitized message
        mock_send_email_task.assert_called_once()
        call_args = mock_send_email_task.call_args[0][0] # call_args[0] is args, [0] is the first arg (email_data)
        sent_message = call_args[4] # message is the 5th element in the email_data tuple
        self.assertEqual(sent_message, expected_sanitized_message)

if __name__ == '__main__':
    unittest.main()
