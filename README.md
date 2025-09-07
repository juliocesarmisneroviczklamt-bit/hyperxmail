# HyperXMail - E-mail Marketing & Campaign Tracking

HyperXMail is a powerful, futuristic-themed bulk email sending application with advanced campaign tracking features. Built with Flask, it provides a web interface to compose, send, and monitor email campaigns, including open and click tracking.

## Features

- **Bulk Email Sending:** Send emails to a large number of recipients via SMTP.
- **Campaign Tracking:** Track email opens and clicks for each campaign.
- **Detailed Reports:** View detailed reports for each campaign, including open and click rates.
- **Rich Text Editor:** Compose beautiful HTML emails with a rich text editor.
- **Email Templates:** Save and load email templates to streamline your workflow.
- **Attachment Support:** Send attachments (images and PDFs) with a size limit of 10MB per file.
- **Embedded Images:** Embed images directly into the email body using `cid`.
- **CSV Upload:** Upload a CSV file with a list of recipients.
- **Secure:**
    - **CSRF Protection:** Built-in CSRF protection to prevent cross-site request forgery attacks.
    - **Input Sanitization:** All user inputs are sanitized to prevent XSS attacks.
    - **Rate Limiting:** Limits the number of emails sent per hour to prevent abuse.

## Project Structure

hyperxmail/
├── app/
│   ├── init.py          # Flask app initialization
│   ├── config.py            # Centralized configuration
│   ├── email_utils.py       # Email sending and tracking logic
│   ├── models.py            # SQLAlchemy database models
│   ├── routes.py            # Flask routes definition
│   ├── template_utils.py    # Template rendering utilities
│   └── templates/
│       ├── index.html       # Main application template
│       └── reports.html     # Reports page template
├── main.py                  # Main application entry point
├── requirements.txt         # Project dependencies
├── .env.example             # Example environment variables file
└── README.md                # This file


## Prerequisites

- Python 3.8 or higher
- An SMTP server (e.g., Office 365, Gmail)
- SMTP credentials (email and password)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <REPOSITORY_URL>
    cd hyperxmail
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the environment variables:**
    Create a `.env` file in the root of the project with the following content:
    ```
    EMAIL_SENDER=your-email@domain.com
    EMAIL_PASSWORD=your-password
    SMTP_SERVER=smtp.office365.com
    SMTP_PORT=587
    ```
    - `EMAIL_SENDER`: The email address that will be used to send the emails.
    - `EMAIL_PASSWORD`: The password for the email account (for Office 365, it might be an app password).
    - `SMTP_SERVER`: The SMTP server address (e.g., `smtp.office365.com` for Office 365).
    - `SMTP_PORT`: The SMTP server port (usually 587 for TLS).

## How to Use

**Warning:** The following command will run the application using Flask's development server. This is not suitable for production environments. For production, you should use a production-ready WSGI server like Gunicorn or uWSGI.

1.  **Run the application:**
    ```bash
    python main.py
    ```
    The server will start at `http://127.0.0.1:5000`.

2.  **Access the web interface:**
    Open your browser and go to `http://127.0.0.1:5000`.

3.  **Compose and send emails:**
    - **Recipients:** Type email addresses manually (press Enter to add) or upload a CSV file with a list of emails (one per line).
    - **Subject:** Enter the email subject.
    - **CC and BCC:** (Optional) Add CC or BCC recipients, separated by commas.
    - **Message:** Compose your message using the rich text editor. You can embed images by uploading them as attachments and then inserting them into the message.
    - **Attachments:** Click on "Attach Files" to add images or PDFs (max 10MB per file).
    - **Templates:** Save your message as a template or load an existing template.
    - **Send:** Click on "Send Broadcast" to send the emails.

4.  **View reports:**
    Click on the "Reports" button to view the campaign reports. You can see the open and click rates for each campaign.

## Troubleshooting

-   **SMTP Authentication Error:**
    -   Double-check your `EMAIL_SENDER` and `EMAIL_PASSWORD` in the `.env` file.
    -   For some email providers (like Office 365), you might need to use an "app password" instead of your regular password.
-   **Emails not being sent:**
    -   Check the console logs for any error messages.
    -   Make sure your SMTP server is accessible and that you haven't exceeded the hourly sending limit.

## Contributing

Feel free to open issues or pull requests with improvements or fixes!

## License

This project is licensed under the MIT License.
