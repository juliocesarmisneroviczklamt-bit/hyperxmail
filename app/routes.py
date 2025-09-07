import logging
import bleach
from flask import jsonify, make_response, request, redirect, render_template
from .email_utils import check_smtp_credentials, send_bulk_emails
import base64
import os
import json
import uuid

# Configura o logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_routes(app):
    # GIF transparente 1x1 para rastreamento
    PIXEL_GIF_DATA = base64.b64decode(b'R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')

    @app.route('/')
    def index():
        tinymce_api_key = app.config.get('TINYMCE_API_KEY', 'no-api-key')
        return render_template('index.html', tinymce_api_key=tinymce_api_key)

    @app.route('/reports')
    def reports():
        return render_template('reports.html')

    @app.route('/templates', methods=['GET'])
    def get_templates():
        templates_file = os.path.join(app.root_path, '..', 'templates.json')
        if not os.path.exists(templates_file):
            return jsonify([])
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        return jsonify(templates)

    @app.route('/templates', methods=['POST'])
    def save_template():
        data = request.get_json()
        if not data or 'name' not in data or 'content' not in data:
            return jsonify({'status': 'error', 'message': 'Dados inválidos.'}), 400

        name = bleach.clean(data['name']).strip()
        # A simple bleach clean for the content, adjust as needed for HTML templates
        content = bleach.clean(data['content'])

        if not name or not content:
            return jsonify({'status': 'error', 'message': 'Nome e conteúdo são obrigatórios.'}), 400

        new_template = {
            'id': str(uuid.uuid4()),
            'name': name,
            'content': content
        }

        templates_file = os.path.join(app.root_path, '..', 'templates.json')
        templates = []
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                try:
                    templates = json.load(f)
                except json.JSONDecodeError:
                    pass  # Trata o caso de arquivo vazio ou corrompido

        templates.append(new_template)

        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=4)

        return jsonify({'status': 'success', 'message': 'Template salvo com sucesso!', 'template': new_template}), 201

    @app.route('/track/open/<email_id>')
    def track_open(email_id):
        from . import db
        from .models import Email, Open
        email = db.session.get(Email, email_id)
        if email:
            new_open = Open(email_id=email.id)
            db.session.add(new_open)
            db.session.commit()

        response = make_response(PIXEL_GIF_DATA)
        response.headers.set('Content-Type', 'image/gif')
        response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
        response.headers.set('Pragma', 'no-cache')
        response.headers.set('Expires', '0')
        return response

    @app.route('/track/click/<email_id>')
    def track_click(email_id):
        from . import db
        from .models import Email, Click
        url = request.args.get('url')
        if not url:
            return "URL não fornecida", 400

        email = db.session.get(Email, email_id)
        if email:
            new_click = Click(email_id=email.id, url=url)
            db.session.add(new_click)
            db.session.commit()

        return redirect(url)

    @app.route('/api/campaigns', methods=['GET'])
    def api_campaigns():
        from .models import Campaign
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        return jsonify([{
            'id': c.id,
            'subject': c.subject,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for c in campaigns])

    @app.route('/api/reports/<int:campaign_id>', methods=['GET'])
    def api_report(campaign_id):
        from . import db
        from .models import Campaign, Email, Open, Click
        campaign = db.get_or_404(Campaign, campaign_id)

        total_sent = len(campaign.emails)
        if total_sent == 0:
            return jsonify({
                'campaign_id': campaign.id,
                'subject': campaign.subject,
                'created_at': campaign.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'total_sent': 0, 'unique_opens': 0, 'unique_clicks': 0,
                'open_rate': '0.00%', 'click_rate': '0.00%'
            })

        unique_opens = db.session.query(Open.email_id).distinct().join(Email).filter(Email.campaign_id == campaign_id).count()
        unique_clicks = db.session.query(Click.email_id).distinct().join(Email).filter(Email.campaign_id == campaign_id).count()

        open_rate = (unique_opens / total_sent) * 100
        click_rate = (unique_clicks / total_sent) * 100

        return jsonify({
            'campaign_id': campaign.id,
            'subject': campaign.subject,
            'created_at': campaign.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'total_sent': total_sent,
            'unique_opens': unique_opens,
            'unique_clicks': unique_clicks,
            'open_rate': f'{open_rate:.2f}%',
            'click_rate': f'{click_rate:.2f}%'
        })

    @app.route('/send_email', methods=['POST'])
    async def send_email():
        if not await check_smtp_credentials():
            logger.error("Falha na autenticação SMTP.")
            return make_response(jsonify({'status': 'error', 'message': 'Falha na autenticação SMTP.'}), 500)

        if not request.is_json:
            return make_response(jsonify({'status': 'error', 'message': 'Requisição inválida.'}), 400)

        data = request.get_json()
        subject = bleach.clean(data.get('subject', '')).strip()
        message = bleach.clean(data.get('message', '')).strip()
        csv_content = data.get('csvContent', '')
        manual_emails = data.get('manualEmails', [])

        if not all([subject, message, csv_content or manual_emails]):
            return make_response(jsonify({'status': 'error', 'message': 'Todos os campos são obrigatórios.'}), 400)

        try:
            base_url = request.host_url
            result = await send_bulk_emails(
                subject=subject,
                cc=bleach.clean(data.get('cc', '')),
                bcc=bleach.clean(data.get('bcc', '')),
                message=message,
                attachments=data.get('attachments', []),
                base_url=base_url,
                csv_content=csv_content,
                manual_emails=manual_emails
            )
            if result['status'] != 'success':
                return make_response(jsonify(result), 500)
            
            return make_response(jsonify(result), 200)

        except Exception as e:
            logger.error(f"Erro na rota /send_email: {e}", exc_info=True)
            return make_response(jsonify({'status': 'error', 'message': 'Erro interno no servidor.'}), 500)
