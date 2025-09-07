import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from app import create_app
from app.models import db, Campaign, Email, Open, Click
import os
import uuid

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app, self.socketio = create_app(testing=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        # Clean up templates.json if it was created
        templates_file = os.path.join(self.app.root_path, '..', 'templates.json')
        if os.path.exists(templates_file):
            os.remove(templates_file)

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('hyperxmail', response.data.decode('utf-8'))

    def test_reports_route(self):
        response = self.client.get('/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Relatórios de Campanhas', response.data.decode('utf-8'))

    def test_get_templates_no_file(self):
        response = self.client.get('/templates')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), [])

    def test_save_and_get_template(self):
        # Save a new template
        template_data = {'name': 'Test Template', 'content': '<p>Hello</p>'}
        response = self.client.post('/templates',
                                    data=json.dumps(template_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Get all templates
        response = self.client.get('/templates')
        self.assertEqual(response.status_code, 200)
        templates = json.loads(response.data)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['name'], 'Test Template')

    def test_save_template_invalid_data(self):
        response = self.client.post('/templates',
                                    data=json.dumps({'name': 'Test'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_track_open(self):
        with self.app.app_context():
            campaign = Campaign(subject='Test Campaign', message='Test Message')
            db.session.add(campaign)
            db.session.commit()
            email = Email(id=str(uuid.uuid4()), campaign_id=campaign.id, recipient='test@example.com')
            db.session.add(email)
            db.session.commit()
            email_id = email.id

        response = self.client.get(f'/track/open/{email_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'image/gif')

        with self.app.app_context():
            self.assertEqual(Open.query.count(), 1)

    def test_track_click(self):
        with self.app.app_context():
            campaign = Campaign(subject='Test Campaign', message='Test Message')
            db.session.add(campaign)
            db.session.commit()
            email = Email(id=str(uuid.uuid4()), campaign_id=campaign.id, recipient='test@example.com')
            db.session.add(email)
            db.session.commit()
            email_id = email.id

        url_to_track = 'http://example.com'
        response = self.client.get(f'/track/click/{email_id}?url={url_to_track}')
        self.assertEqual(response.status_code, 302) # Redirect
        self.assertEqual(response.location, url_to_track)

        with self.app.app_context():
            self.assertEqual(Click.query.count(), 1)
            self.assertEqual(Click.query.first().url, url_to_track)

    def test_api_campaigns(self):
        with self.app.app_context():
            campaign1 = Campaign(subject='Campaign 1', message='Message 1')
            campaign2 = Campaign(subject='Campaign 2', message='Message 2')
            db.session.add_all([campaign1, campaign2])
            db.session.commit()

        response = self.client.get('/api/campaigns')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['subject'], 'Campaign 2') # Test order_by desc

    def test_api_report(self):
        with self.app.app_context():
            campaign = Campaign(subject='Test Campaign', message='Test Message')
            db.session.add(campaign)
            db.session.commit()
            email = Email(id=str(uuid.uuid4()), campaign_id=campaign.id, recipient='test@example.com')
            db.session.add(email)
            db.session.commit()
            open_event = Open(email_id=email.id)
            click_event = Click(email_id=email.id, url='http://example.com')
            db.session.add_all([open_event, click_event])
            db.session.commit()
            campaign_id = campaign.id

        response = self.client.get(f'/api/reports/{campaign_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_sent'], 1)
        self.assertEqual(data['unique_opens'], 1)
        self.assertEqual(data['unique_clicks'], 1)
        self.assertEqual(data['open_rate'], '100.00%')
        self.assertEqual(data['click_rate'], '100.00%')

    def test_api_report_no_sends(self):
        with self.app.app_context():
            campaign = Campaign(subject='Test Campaign', message='Test Message')
            db.session.add(campaign)
            db.session.commit()
            campaign_id = campaign.id

        response = self.client.get(f'/api/reports/{campaign_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total_sent'], 0)

    @patch('app.routes.check_smtp_credentials', new_callable=AsyncMock)
    @patch('app.routes.send_bulk_emails', new_callable=AsyncMock)
    def test_send_email_success(self, mock_send_bulk_emails, mock_check_smtp):
        mock_check_smtp.return_value = True
        mock_send_bulk_emails.return_value = {'status': 'success'}

        email_data = {
            'subject': 'Test Subject',
            'message': 'Test Message',
            'manualEmails': ['test@example.com']
        }

        response = self.client.post('/send_email',
                                         data=json.dumps(email_data),
                                         content_type='application/json')

        self.assertEqual(response.status_code, 200)
        mock_send_bulk_emails.assert_called_once()

    @patch('app.routes.check_smtp_credentials', new_callable=AsyncMock)
    def test_send_email_smtp_failure(self, mock_check_smtp):
        mock_check_smtp.return_value = False

        email_data = {
            'subject': 'Test Subject',
            'message': 'Test Message',
            'manualEmails': ['test@example.com']
        }

        response = self.client.post('/send_email',
                                         data=json.dumps(email_data),
                                         content_type='application/json')

        self.assertEqual(response.status_code, 500)
        self.assertIn(b'Falha na autentica', response.data)

    @patch('app.routes.check_smtp_credentials', new_callable=AsyncMock)
    def test_send_email_invalid_request(self, mock_check_smtp):
        mock_check_smtp.return_value = True
        response = self.client.post('/send_email', data="not json", content_type='text/plain')
        self.assertEqual(response.status_code, 400)

    @patch('app.routes.check_smtp_credentials', new_callable=AsyncMock)
    def test_send_email_missing_fields(self, mock_check_smtp):
        mock_check_smtp.return_value = True

        response = self.client.post('/send_email',
                                         data=json.dumps({'subject': 'Test'}),
                                         content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Todos os campos s', response.data)

if __name__ == '__main__':
    unittest.main()
