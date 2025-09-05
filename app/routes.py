import logging
import bleach
from flask import jsonify, make_response, request  # Adicionada a importação de request
from .email_utils import check_smtp_credentials, send_bulk_emails
from .templates import get_index_template
from flask import redirect, jsonify
import base64

# Configura o logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_auth(token, expected_token):
    """
    Verifica se o token de autenticação é válido.

    Args:
        token (str): Token fornecido na requisição.
        expected_token (str): Token esperado configurado no sistema.

    Returns:
        bool: True se o token for válido, False caso contrário.
    """
    return token == expected_token

def init_routes(app):
    # 1x1 transparent GIF
    PIXEL_GIF_DATA = base64.b64decode(b'R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')

    @app.route('/track/open/<email_id>')
    def track_open(email_id):
        from . import db
        from .models import Email, Open
        email = Email.query.get(email_id)
        if email:
            new_open = Open(email_id=email.id)
            db.session.add(new_open)
            db.session.commit()

        response = make_response(PIXEL_GIF_DATA)
        response.headers['Content-Type'] = 'image/gif'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/track/click/<email_id>')
    def track_click(email_id):
        from . import db
        from .models import Email, Click
        url = request.args.get('url')
        if not url:
            return "URL não fornecida", 400

        email = Email.query.get(email_id)
        if email:
            new_click = Click(email_id=email.id, url=url)
            db.session.add(new_click)
            db.session.commit()

        return redirect(url)

    @app.route('/api/campaigns')
    def api_campaigns():
        from .models import Campaign
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        return jsonify([{
            'id': c.id,
            'subject': c.subject,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for c in campaigns])

    @app.route('/api/reports/<int:campaign_id>')
    def api_report(campaign_id):
        from . import db
        from .models import Campaign, Email, Open, Click
        campaign = Campaign.query.get_or_404(campaign_id)

        total_sent = len(campaign.emails)

        # Contagem de aberturas únicas por e-mail
        unique_opens = db.session.query(Open.email_id).distinct().filter(Email.campaign_id == campaign_id).join(Email).count()

        # Contagem de cliques únicos por e-mail
        unique_clicks = db.session.query(Click.email_id).distinct().filter(Email.campaign_id == campaign_id).join(Email).count()

        open_rate = (unique_opens / total_sent) * 100 if total_sent > 0 else 0
        click_rate = (unique_clicks / total_sent) * 100 if total_sent > 0 else 0

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
    """
    Registra as rotas na aplicação Flask.

    Args:
        app (Flask): Instância da aplicação Flask.
    """
    @app.route('/')
    def index():
        """
        Rota principal que renderiza a interface web.

        Returns:
            str: HTML renderizado da interface.
        """
        return get_index_template(app.config['API_TOKEN'])

    @app.route('/reports')
    def reports():
        from .templates import get_reports_template
        return get_reports_template()

    @app.route('/send_email', methods=['POST'])
    async def send_email():
        """
        Rota para envio de e-mails em massa.

        Returns:
            Response: Resposta JSON com o resultado do envio.
        """
        logger.debug("Recebida requisição para /send_email")
        
        # Verifica as credenciais SMTP
        if not check_smtp_credentials():
            logger.error("Falha na autenticação SMTP.")
            return make_response(jsonify({'status': 'error', 'message': 'Falha na autenticação SMTP.'}), 500)

        # Verifica a autenticação
        auth_token = request.headers.get('Authorization')
        logger.debug(f"Token de autenticação recebido: {auth_token}")
        if not auth_token or not check_auth(auth_token, app.config['API_TOKEN']):
            logger.error(f"Falha na autenticação: Token recebido={auth_token}, esperado={app.config['API_TOKEN']}")
            return make_response(jsonify({'status': 'error', 'message': 'Unauthorized'}), 401)

        try:
            if not request.is_json:
                logger.error("Requisição não contém JSON válido.")
                return make_response(jsonify({'status': 'error', 'message': 'Requisição inválida: conteúdo não é JSON.'}), 400)

            data = request.get_json()
            logger.debug(f"Dados recebidos: {data}")
            subject = bleach.clean(data.get('subject', ''))
            cc = bleach.clean(data.get('cc', ''))
            bcc = bleach.clean(data.get('bcc', ''))
            message = data.get('message', '')
            attachments = data.get('attachments', [])
            csv_content = data.get('csvContent', '')
            manual_emails = data.get('manualEmails', [])

            # Validações básicas
            if not subject.strip():
                logger.error("Assunto vazio.")
                return make_response(jsonify({'status': 'error', 'message': 'O assunto é obrigatório.'}), 400)
            if not message.strip():
                logger.error("Mensagem vazia.")
                return make_response(jsonify({'status': 'error', 'message': 'A mensagem não pode estar vazia.'}), 400)
            if not csv_content and not manual_emails:
                logger.error("Nenhum destinatário fornecido.")
                return make_response(jsonify({'status': 'error', 'message': 'Nenhum destinatário ou CSV fornecido.'}), 400)

            logger.debug("Iniciando envio em massa...")
            # Envia os e-mails em massa
            base_url = request.host_url
            result = await send_bulk_emails(subject, cc, bcc, message, attachments, base_url, csv_content, manual_emails)
            if result['status'] != 'success':
                logger.error(f"Falha no envio em massa: {result['message']}")
                return make_response(jsonify(result), 500)

            logger.info("Envio em massa concluído com sucesso no backend.")
            return make_response(jsonify({'status': 'success', 'message': 'Envio em massa concluído com sucesso.'}), 200)
        except Exception as e:
            logger.error(f"Erro geral na rota /send_email: {str(e)}", exc_info=True)
            return make_response(jsonify({'status': 'error', 'message': f'Erro interno no servidor: {str(e)}'}), 500)