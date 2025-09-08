import unittest
import asyncio
import base64
from unittest.mock import patch, AsyncMock
from app import create_app
from app.email_utils import send_email_task

# A simple 1x1 pixel PNG for testing purposes, encoded in Base64.
TEST_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

class ImageEmbeddingTestCase(unittest.TestCase):
    """
    Test case for verifying the image embedding logic in emails.
    """
    def setUp(self):
        """
        Set up the test environment before each test.
        This creates a new Flask application instance in testing mode.
        """
        self.app, self.socketio = create_app(testing=True)

    @patch('app.email_utils.aiosmtplib.SMTP')
    def test_image_is_embedded_even_with_mismatched_alt_text(self, mock_smtp_class):
        """
        Tests that an image is correctly embedded (using CID) in the email body
        even when the <img> tag's alt attribute does not match the attachment's filename.

        This test simulates a realistic scenario where a user adds an image and then
        changes the alt text, which caused the old logic to fail.
        """
        # As send_email_task is an async function, we define and run an async test block.
        async def run_test():
            # Arrange: Configure the mock for the async context manager.
            mock_smtp_instance = AsyncMock()
            # When `aiosmtplib.SMTP()` is called, it returns a mock object.
            # When that mock is used in an `async with` statement, its `__aenter__` method is awaited.
            # We configure that method to return our `mock_smtp_instance`. This ensures that the
            # `client` variable inside `send_email_task` is our mock instance.
            mock_smtp_class.return_value.__aenter__.return_value = mock_smtp_instance

            # Arrange: Define test data
            html_body = '<p>Check out this image:</p><img src="placeholder.jpg" alt="A nice picture">'
            attachment = {
                'name': 'test-image.png',
                'data': TEST_IMAGE_B64
            }
            email_data = (
                ['recipient@example.com'],  # to
                'Test Subject',             # subject
                '',                         # cc
                '',                         # bcc
                html_body,                  # message
                [attachment],               # attachments
                'test-email-id-12345'       # email_id
            )
            base_url = 'http://localhost:5000/'

            # Act: Call the function under test
            with self.app.app_context():
                await send_email_task(email_data, base_url)

            # Assert: Verify the outcome
            # 1. Check that the `send_message` method on our instance was called.
            mock_smtp_instance.send_message.assert_called_once()

            # 2. Extract the sent message payload.
            sent_msg = mock_smtp_instance.send_message.call_args[0][0]

            # 3. Find the HTML and image parts of the multipart email.
            html_part, image_part = None, None
            related_part = sent_msg.get_payload(0)
            self.assertEqual(related_part.get_content_type(), 'multipart/related')
            for part in related_part.walk():
                if part.get_content_type() == 'text/html':
                    html_part = part
                elif part.get_content_type() == 'image/png':
                    image_part = part

            self.assertIsNotNone(html_part, "The HTML part was not found in the email.")
            self.assertIsNotNone(image_part, "The image part was not found in the email.")

            # 4. Get the Content-ID (CID) from the image part.
            content_id = image_part.get('Content-ID').strip('<>')

            # 5. Verify the HTML body was correctly modified.
            final_html = html_part.get_payload(decode=True).decode('utf-8')

            # This is the crucial assertion that should fail due to the bug.
            # A passing test means the src was rewritten to use the CID.
            expected_img_tag_src = f'src="cid:{content_id}"'
            self.assertIn(expected_img_tag_src, final_html, "The <img> tag's src was not replaced with the correct CID.")
            self.assertNotIn('src="placeholder.jpg"', final_html, "The original placeholder src should have been removed.")
            self.assertIn('alt="A nice picture"', final_html, "The original alt text was not preserved.")

        # Run the async test function.
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
