import asyncio
import os
import base64
import logging
import smtplib
import tempfile
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import mimetypes
import bleach
import re
from .config import Config

# Configura o logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Regex para validação de e-mails
email_regex = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', re.IGNORECASE)

# Tipos de anexo permitidos
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'application/pdf']

def check_smtp_credentials():
    """
    Verifica se as credenciais SMTP estão corretas.

    Returns:
        bool: True se as credenciais estiverem corretas, False caso contrário.
    """
    try:
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        logger.info("Credenciais SMTP verificadas com sucesso.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro de autenticação SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar credenciais SMTP: {e}")
        return False

async def send_email_task(email_data):
    """
    Envia um e-mail assincronamente para um grupo de destinatários.

    Args:
        email_data (tuple): Dados do e-mail (destinatários, assunto, CC, CCO, mensagem, anexos).

    Returns:
        dict: Resultado do envio com status e mensagem.
    """
    to, subject, cc, bcc, message, attachments = email_data
    saved_files = []

    try:
        # Filtra e valida os destinatários
        to = [str(email).strip() for email in to if email_regex.match(str(email).strip())]
        if not to:
            logger.error("Nenhum destinatário válido fornecido.")
            return {'status': 'error', 'message': 'Nenhum destinatário válido fornecido.'}

        # Cria a mensagem multipart alternativa como base
        msg = MIMEMultipart('alternative')
        msg['Subject'] = bleach.clean(subject)
        msg['From'] = Config.EMAIL_SENDER
        msg['To'] = ', '.join([bleach.clean(email) for email in to])
        if cc:
            msg['Cc'] = bleach.clean(cc)
        if bcc:
            msg['Bcc'] = bleach.clean(bcc)

        # Cria uma subparte related para o corpo HTML e imagens embutidas
        msg_related = MIMEMultipart('related')
        msg.attach(msg_related)

        # Sanitiza a mensagem permitindo tags e atributos comuns de rich text
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span',
            'img', 'a', 'code'
        ]
        allowed_attributes = {
            '*': ['style'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'a': ['href', 'target', 'title'],
            'td': ['align'],
            'th': ['align']
        }
        sanitized_message = bleach.clean(message, tags=allowed_tags, attributes=allowed_attributes)

        # Adiciona o HTML como corpo principal
        html_message = f'<html><body>{sanitized_message}</body></html>'
        html_part = MIMEText(html_message, 'html')
        msg_related.attach(html_part)

        # Processa anexos e vincula imagens ao HTML via cid
        if attachments:
            for i, att in enumerate(attachments):
                cid = f'image-{uuid.uuid4()}'  # Gera um Content-ID único
                # Substitui ou adiciona src com cid à tag <img> baseada no alt
                if f'cid:image{i}' in sanitized_message:
                    # Substituir mesmo quando a imagem está dentro de uma tag <a>
                    sanitized_message = sanitized_message.replace(f'cid:image{i}', f'cid:{cid}')
                else:
                    sanitized_message = sanitized_message.replace(
                        f'<img alt="{att["name"]}"',
                        f'<img src="cid:{cid}" alt="{att["name"]}"'
                    )
                
                # Atualiza o HTML no corpo
                html_message = f'<html><body>{sanitized_message}</body></html>'
                html_part.set_payload(html_message)

                # Decodifica o base64 e verifica o tamanho
                decoded_data = base64.b64decode(att['data'])
                file_size = len(decoded_data)
                if file_size > Config.MAX_ATTACHMENT_SIZE:
                    logger.error(f"Anexo {att['name']} excede o limite de {Config.MAX_ATTACHMENT_SIZE} bytes.")
                    return {'status': 'error', 'message': f"Anexo {att['name']} excede o limite de 10MB."}
                
                # Verifica o tipo MIME do anexo
                mime_type, _ = mimetypes.guess_type(att['name'])
                if mime_type not in ALLOWED_MIME_TYPES:
                    logger.error(f"Tipo de anexo não permitido: {mime_type}")
                    return {'status': 'error', 'message': f"Tipo de anexo não permitido: {att['name']}"}
                
                # Salva o arquivo temporário
                suffix = '.' + att['name'].split('.')[-1]
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                    tmp_file.write(decoded_data)
                    saved_files.append(tmp_file.name)

                # Anexa como imagem embutida ou anexo normal
                if mime_type.startswith('image/'):
                    with open(tmp_file.name, 'rb') as img_file:
                        img = MIMEImage(img_file.read())
                        img.add_header('Content-ID', f'<{cid}>')
                        img.add_header('Content-Disposition', 'inline', filename=att['name'])
                        msg_related.attach(img)
                else:
                    with open(tmp_file.name, 'rb') as file:
                        part = MIMEApplication(file.read(), Name=att['name'])
                        part['Content-Disposition'] = f'attachment; filename="{att["name"]}"'
                        msg.attach(part)

        logger.debug(f"HTML gerado para o e-mail: {html_message}")
        
        # Envia o e-mail
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10) as servidor:
            servidor.starttls()
            logger.info(f"Tentando login com {Config.EMAIL_SENDER}...")
            servidor.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            servidor.send_message(msg)
            logger.info(f"E-mail enviado para {', '.join(to)}")

        await asyncio.sleep(Config.SECONDS_PER_EMAIL)
        with open('sent_emails.log', 'a') as log_file:
            log_file.write(f"{','.join(to)}\n")
        return {'status': 'success', 'message': 'E-mail enviado com sucesso!'}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro de autenticação SMTP: {e}")
        return {'status': 'error', 'message': f"Erro de autenticação: {str(e)}"}
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {to}: {e}")
        return {'status': 'error', 'message': str(e)}
    finally:
        # Limpeza de arquivos temporários
        for filepath in saved_files:
            try:
                os.remove(filepath)
                logger.info(f"Anexo temporário removido: {filepath}")
            except Exception as e:
                logger.error(f"Erro ao remover arquivo temporário {filepath}: {e}")

async def send_bulk_emails(subject, cc, bcc, message, attachments, csv_content=None, manual_emails=None):
    """
    Envia e-mails em massa para uma lista de destinatários.

    Args:
        subject (str): Assunto do e-mail.
        cc (str): Endereços de e-mail em cópia (separados por vírgulas).
        bcc (str): Endereços de e-mail em cópia oculta (separados por vírgulas).
        message (str): Corpo da mensagem (pode conter HTML com imagens).
        attachments (list): Lista de anexos (imagens ou PDFs).
        csv_content (str, optional): Conteúdo de um arquivo CSV com e-mails.
        manual_emails (list, optional): Lista de e-mails adicionados manualmente.

    Returns:
        dict: Resultado do envio em massa com status e mensagem.
    """
    try:
        # Extrai e-mails do CSV e da lista manual
        all_emails = set()
        if csv_content:
            all_emails.update(line.strip() for line in csv_content.splitlines() if email_regex.match(line.strip()))
        if manual_emails:
            all_emails.update(email.strip() for email in manual_emails if email_regex.match(email.strip()))

        logger.debug(f"E-mails extraídos: {all_emails}")
        if not all_emails:
            logger.error("Nenhum e-mail válido encontrado.")
            return {'status': 'error', 'message': "Nenhum e-mail válido encontrado."}

        # Carrega e-mails já enviados para evitar duplicatas
        sent_emails = set()
        if os.path.exists('sent_emails.log'):
            with open('sent_emails.log', 'r') as log_file:
                sent_emails = set(line.strip() for line in log_file if line.strip())
            logger.debug(f"E-mails já enviados (sent_emails.log): {sent_emails}")

        emails_to_send = [[email] for email in all_emails if email not in sent_emails]
        logger.info(f"Enviando {len(emails_to_send)} e-mails restantes...")

        if not emails_to_send:
            logger.warning("Todos os e-mails já foram enviados anteriormente.")
            return {'status': 'success', 'message': "Nenhum novo e-mail para enviar (todos já enviados)."}

        # Cria tarefas assíncronas para enviar os e-mails
        tasks = [send_email_task((batch, subject, cc, bcc, message, attachments)) for batch in emails_to_send]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verifica os resultados das tarefas
        for result in results:
            if isinstance(result, dict) and result['status'] != 'success':
                logger.error(f"Falha ao enviar e-mail: {result['message']}")
                return result

        return {'status': 'success', 'message': f"Enviados {len(emails_to_send)} e-mails."}
    except Exception as e:
        logger.error(f"Erro no envio em massa: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}