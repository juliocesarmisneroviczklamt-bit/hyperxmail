"""Definição das rotas e endpoints da aplicação Flask.

Este módulo contém toda a lógica de roteamento da aplicação, incluindo:
- Rotas para renderizar as páginas principais da interface do usuário (HTML).
- Endpoints de API para operações de dados (JSON), como buscar campanhas e relatórios.
- Endpoints de serviço, como o envio de e-mails e o salvamento de templates.
- Rotas de rastreamento para registrar aberturas e cliques de e-mail.
"""
import logging
import bleach
from flask import jsonify, make_response, request, redirect, render_template
from .email_utils import check_smtp_credentials, send_bulk_emails
from .utils import sanitize_html
import base64
import os
import json
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_routes(app):
    """Inicializa todas as rotas da aplicação.

    Args:
        app (Flask): A instância da aplicação Flask.
    """
    # GIF transparente de 1x1 pixel, usado para rastrear aberturas de e-mail.
    # É um método comum e eficaz para registrar quando um e-mail é visualizado.
    PIXEL_GIF_DATA = base64.b64decode(b'R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')

    @app.route('/')
    def index():
        """Renderiza a página inicial da aplicação (página de envio).

        Fornece a chave da API do TinyMCE ao template para inicializar o editor
        de rich text.

        Returns:
            str: O conteúdo HTML da página `index.html`.
        """
        tinymce_api_key = app.config.get('TINYMCE_API_KEY', 'no-api-key')
        return render_template('index.html', tinymce_api_key=tinymce_api_key)

    @app.route('/reports')
    def reports():
        """Renderiza a página de relatórios de campanhas.

        Returns:
            str: O conteúdo HTML da página `reports.html`.
        """
        return render_template('reports.html')

    @app.route('/templates', methods=['GET'])
    def get_templates():
        """Endpoint da API para obter a lista de templates de e-mail salvos.

        Lê os templates de um arquivo `templates.json`.

        Returns:
            Response: Uma resposta JSON contendo uma lista de objetos de template.
                      Retorna uma lista vazia se o arquivo não existir.
        """
        templates_filename = app.config.get('TEMPLATES_FILE_PATH', 'templates.json')
        templates_file = os.path.join(app.root_path, '..', templates_filename)
        if not os.path.exists(templates_file):
            return jsonify([])
        with open(templates_file, 'r') as f:
            templates = json.load(f)
        return jsonify(templates)

    @app.route('/templates', methods=['POST'])
    def save_template():
        """Endpoint da API para salvar um novo template de e-mail.

        Recebe o nome e o conteúdo do template via JSON, sanitiza os dados,
        gera um ID único e o salva no arquivo `templates.json`.

        Returns:
            Response: Uma resposta JSON com status de sucesso ou erro.
        """
        data = request.get_json()
        if not data or 'name' not in data or 'content' not in data:
            return jsonify({'status': 'error', 'message': 'Dados inválidos.'}), 400

        name = bleach.clean(data['name']).strip()
        content = sanitize_html(data['content'])

        if not name or not content:
            return jsonify({'status': 'error', 'message': 'Nome e conteúdo são obrigatórios.'}), 400

        new_template = {'id': str(uuid.uuid4()), 'name': name, 'content': content}

        templates_filename = app.config.get('TEMPLATES_FILE_PATH', 'templates.json')
        templates_file = os.path.join(app.root_path, '..', templates_filename)
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
        """Endpoint de rastreamento de abertura de e-mail.

        Quando o pixel de rastreamento em um e-mail é carregado, esta rota é
        acionada. Ela registra um evento de `Open` no banco de dados para o
        `email_id` correspondente.

        Args:
            email_id (str): O ID único do e-mail que foi aberto.

        Returns:
            Response: Uma resposta de imagem GIF 1x1 com headers que desativam
                      o cache.
        """
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
        """Endpoint de rastreamento de clique em link.

        Quando um link rastreável é clicado, esta rota registra um evento de
        `Click` no banco de dados e redireciona o usuário para a URL original.

        Args:
            email_id (str): O ID único do e-mail onde o clique ocorreu.

        Returns:
            Response: Um redirecionamento para a URL de destino original.
                      Retorna um erro 400 se a URL não for fornecida.
        """
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
        """Endpoint da API para listar todas as campanhas.

        Retorna uma lista de todas as campanhas ordenadas pela data de criação.

        Returns:
            Response: Uma resposta JSON com a lista de campanhas.
        """
        from .models import Campaign
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        return jsonify([
            {'id': c.id, 'subject': c.subject, 'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            for c in campaigns
        ])

    @app.route('/api/reports/<int:campaign_id>', methods=['GET'])
    def api_report(campaign_id):
        """Endpoint da API para obter o relatório de uma campanha específica.

        Calcula as métricas da campanha, como total de envios, aberturas únicas,
        cliques únicos e as respectivas taxas.

        Args:
            campaign_id (int): O ID da campanha a ser analisada.

        Returns:
            Response: Uma resposta JSON com os dados detalhados do relatório.
        """
        from . import db
        from .models import Campaign, Email, Open, Click
        campaign = db.get_or_404(Campaign, campaign_id)

        total_sent = len(campaign.emails)
        if total_sent == 0:
            return jsonify({
                'campaign_id': campaign.id, 'subject': campaign.subject,
                'created_at': campaign.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'total_sent': 0, 'unique_opens': 0, 'unique_clicks': 0,
                'open_rate': '0.00%', 'click_rate': '0.00%'
            })

        unique_opens = db.session.query(Open.email_id).distinct().join(Email).filter(Email.campaign_id == campaign_id).count()
        unique_clicks = db.session.query(Click.email_id).distinct().join(Email).filter(Email.campaign_id == campaign_id).count()

        open_rate = (unique_opens / total_sent) * 100 if total_sent > 0 else 0
        click_rate = (unique_clicks / total_sent) * 100 if total_sent > 0 else 0

        return jsonify({
            'campaign_id': campaign.id, 'subject': campaign.subject,
            'created_at': campaign.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'total_sent': total_sent, 'unique_opens': unique_opens,
            'unique_clicks': unique_clicks, 'open_rate': f'{open_rate:.2f}%',
            'click_rate': f'{click_rate:.2f}%'
        })

    @app.route('/send_email', methods=['POST'])
    async def send_email():
        """Endpoint principal para iniciar o envio de uma campanha de e-mail.

        Esta é uma rota assíncrona que:
        1. Verifica as credenciais SMTP.
        2. Valida e sanitiza os dados recebidos (assunto, mensagem, destinatários).
        3. Invoca a função `send_bulk_emails` para orquestrar o envio.

        Returns:
            Response: Uma resposta JSON indicando o sucesso ou a falha da
                      solicitação de envio.
        """
        if not await check_smtp_credentials():
            logger.error("Falha na autenticação SMTP.")
            return make_response(jsonify({'status': 'error', 'message': 'Falha na autenticação SMTP.'}), 500)

        if not request.is_json:
            return make_response(jsonify({'status': 'error', 'message': 'Requisição inválida.'}), 400)

        data = request.get_json()
        subject = bleach.clean(data.get('subject', '')).strip()
        message = data.get('message', '')
        csv_content = data.get('csvContent', '')
        manual_emails = data.get('manualEmails', [])

        if not all([subject, message, csv_content or manual_emails]):
            return make_response(jsonify({'status': 'error', 'message': 'Todos os campos são obrigatórios.'}), 400)

        try:
            result = await send_bulk_emails(
                subject=subject,
                cc=bleach.clean(data.get('cc', '')),
                bcc=bleach.clean(data.get('bcc', '')),
                message=message,
                attachments=data.get('attachments', []),
                base_url=request.host_url,
                csv_content=csv_content,
                manual_emails=manual_emails
            )
            status_code = 200 if result['status'] == 'success' else 500
            return make_response(jsonify(result), status_code)

        except Exception as e:
            logger.error(f"Erro na rota /send_email: {e}", exc_info=True)
            return make_response(jsonify({'status': 'error', 'message': 'Erro interno no servidor.'}), 500)
