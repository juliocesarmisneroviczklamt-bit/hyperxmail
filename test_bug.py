import pytest
import re
from app.email_utils import email_regex

def test_email_validation_is_case_insensitive():
    """
    Tests that the email validation regex is case-insensitive.
    """
    # This email should be valid, but will fail with the current regex
    email_with_uppercase = "Test@Example.com"

    # The test will fail here because the current regex is case-sensitive
    assert email_regex.match(email_with_uppercase) is not None, "Email with uppercase letters should be valid"
