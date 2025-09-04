import logging
import bleach
from flask import jsonify, make_response, request  # Adicionada a importação de request
from .email_utils import check_smtp_credentials, send_bulk_emails
from .templates import get_index_template

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
            result = await send_bulk_emails(subject, cc, bcc, message, attachments, csv_content, manual_emails)
            if result['status'] != 'success':
                logger.error(f"Falha no envio em massa: {result['message']}")
                return make_response(jsonify(result), 500)

            logger.info("Envio em massa concluído com sucesso no backend.")
            return make_response(jsonify({'status': 'success', 'message': 'Envio em massa concluído com sucesso.'}), 200)
        except Exception as e:
            logger.error(f"Erro geral na rota /send_email: {str(e)}", exc_info=True)
            return make_response(jsonify({'status': 'error', 'message': f'Erro interno no servidor: {str(e)}'}), 500)