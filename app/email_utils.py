"""Utilitários para envio de e-mails e manipulação de conteúdo.

Este módulo fornece funções assíncronas para:
- Verificar credenciais SMTP.
- Enviar e-mails individuais com suporte a HTML, anexos e rastreamento.
- Orquestrar o envio de e-mails em massa para campanhas.
- Realizar a sanitização de nomes de arquivos e conteúdo HTML.
"""
import asyncio
import os
import base64
import logging
import aiosmtplib
import tempfile
import uuid
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import magic
import bleach
import re
from bs4 import BeautifulSoup
from .config import Config
from .utils import sanitize_html

# Configuração do logging para este módulo.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Expressão regular para uma validação básica de endereços de e-mail.
email_regex = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', re.IGNORECASE)

# Lista de tipos MIME permitidos para anexos, para fins de segurança.
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'application/pdf']

def sanitize_filename(filename):
    """Sanitiza um nome de arquivo para remover caracteres potencialmente perigosos.

    Remove caracteres que não são alfanuméricos, pontos, hífens ou underscores
    para prevenir ataques como Path Traversal e Cross-Site Scripting (XSS).

    Args:
        filename (str): O nome do arquivo original.

    Returns:
        str: O nome do arquivo sanitizado.
    """
    # Define the set of allowed characters
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"

    # Filter the filename to keep only allowed characters
    return ''.join(c for c in filename if c in allowed_chars)

async def check_smtp_credentials():
    """Verifica de forma assíncrona a validade das credenciais SMTP.

    Tenta conectar e autenticar no servidor SMTP configurado na `Config`.
    Isso é útil para validar as configurações antes de iniciar um envio em massa.

    Returns:
        bool: True se a autenticação for bem-sucedida, False caso contrário.
    """
    try:
        client = aiosmtplib.SMTP(hostname=Config.SMTP_SERVER, port=Config.SMTP_PORT, use_tls=False)
        await client.connect()
        await client.starttls()
        await client.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        await client.quit()
        logger.info("Credenciais SMTP verificadas com sucesso.")
        return True
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro de autenticação SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar credenciais SMTP: {e}")
        return False

async def send_email_task(email_data, base_url):
    """Envia um único e-mail de forma assíncrona.

    Esta função constrói e envia um e-mail multipart, lidando com:
    - HTML e sanitização.
    - Anexos (validação de tipo e tamanho).
    - Imagens embutidas (via Content-ID).
    - Rastreamento de aberturas (pixel de rastreamento).
    - Rastreamento de cliques (reescrita de links).

    Args:
        email_data (tuple): Uma tupla contendo os detalhes do e-mail:
            (to, subject, cc, bcc, message, attachments, email_id).
            - to (list[str]): Lista de destinatários.
            - subject (str): Assunto do e-mail.
            - cc (str): Destinatários em cópia.
            - bcc (str): Destinatários em cópia oculta.
            - message (str): Corpo da mensagem em HTML.
            - attachments (list[dict]): Lista de anexos.
            - email_id (str): UUID único para este e-mail.
        base_url (str): A URL base da aplicação, usada para construir os links
            de rastreamento.

    Returns:
        dict: Um dicionário com o status (`'success'` ou `'error'`) e uma
              mensagem descritiva.
    """
    to, subject, cc, bcc, message, attachments, email_id = email_data
    saved_files = []

    try:
        to = [str(email).strip() for email in to if email_regex.match(str(email).strip())]
        if not to:
            return {'status': 'error', 'message': 'Nenhum destinatário válido fornecido.'}

        msg = MIMEMultipart('alternative')
        msg['Subject'] = bleach.clean(subject)
        msg['From'] = Config.EMAIL_SENDER
        msg['To'] = ', '.join([bleach.clean(email) for email in to])
        if cc: msg['Cc'] = cc
        if bcc: msg['Bcc'] = bcc

        msg_related = MIMEMultipart('related')
        msg.attach(msg_related)

        # Parse the HTML message once to allow for robust modifications.
        soup = BeautifulSoup(message, 'html.parser')

        # Rewrite links for click tracking.
        for a in soup.find_all('a', href=True):
            # Only track absolute URLs.
            if a['href'].startswith('http'):
                original_url = urllib.parse.quote(a['href'], safe='')
                a['href'] = f"{base_url}track/click/{email_id}?url={original_url}"

        # Process attachments, embedding images that have a corresponding <img> tag.
        if attachments:
            img_tags = soup.find_all('img')
            img_tag_index = 0

            for att in attachments:
                sanitized_filename = sanitize_filename(att['name']) or "attachment"
                decoded_data = base64.b64decode(att['data'])

                if len(decoded_data) > Config.MAX_ATTACHMENT_SIZE:
                    return {'status': 'error', 'message': f"Anexo {sanitized_filename} excede o limite de 10MB."}
                
                mime_type = magic.from_buffer(decoded_data, mime=True)
                if mime_type not in ALLOWED_MIME_TYPES:
                    return {'status': 'error', 'message': f"Tipo de anexo não permitido: {sanitized_filename}"}
                
                # If the attachment is an image and there's a corresponding <img> tag, embed it.
                if mime_type.startswith('image/') and img_tag_index < len(img_tags):
                    cid = f'image-{uuid.uuid4()}'
                    img = MIMEImage(decoded_data)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=sanitized_filename)
                    msg_related.attach(img)

                    # Update the src of the corresponding img tag.
                    img_tags[img_tag_index]['src'] = f'cid:{cid}'
                    img_tag_index += 1
                else:
                    # Otherwise, add it as a regular attachment.
                    part = MIMEApplication(decoded_data, Name=sanitized_filename)
                    part['Content-Disposition'] = f'attachment; filename="{sanitized_filename}"'
                    msg.attach(part)

        # Add the tracking pixel to the end of the body.
        tracking_pixel_tag = BeautifulSoup(
            f'<img src="{base_url}track/open/{email_id}" width="1" height="1" alt="">',
            'html.parser'
        )
        if soup.body:
            soup.body.append(tracking_pixel_tag)
        else:
            soup.append(tracking_pixel_tag)

        # Attach the final, modified HTML to the email.
        final_html = str(soup)
        sanitized_html = sanitize_html(final_html)
        html_part = MIMEText(sanitized_html, 'html')
        msg_related.attach(html_part)
        
        async with aiosmtplib.SMTP(hostname=Config.SMTP_SERVER, port=Config.SMTP_PORT, use_tls=False) as client:
            await client.starttls()
            await client.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            await client.send_message(msg)
            logger.info(f"E-mail enviado para {', '.join(to)}")

        await asyncio.sleep(Config.SECONDS_PER_EMAIL)
        return {'status': 'success', 'message': 'E-mail enviado com sucesso!'}

    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro de autenticação SMTP: {e}")
        return {'status': 'error', 'message': f"Erro de autenticação: {str(e)}"}
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {to}: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}
    finally:
        for filepath in saved_files:
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Erro ao remover arquivo temporário {filepath}: {e}")

async def send_bulk_emails(subject, cc, bcc, message, attachments, base_url, csv_content=None, manual_emails=None):
    """Orquestra o envio de e-mails em massa para uma campanha.

    Esta função gerencia todo o fluxo de uma campanha de e-mail:
    1. Cria um registro de `Campaign` no banco de dados.
    2. Extrai e valida os e-mails de destino a partir de conteúdo CSV e/ou uma lista manual.
    3. Para cada e-mail, cria um registro `Email` no banco de dados.
    4. Invoca `send_email_task` para enviar cada e-mail individualmente.
    5. Emite eventos de progresso via SocketIO para o frontend.
    6. Em caso de falha, emite um evento de erro.

    Args:
        subject (str): O assunto do e-mail da campanha.
        cc (str): String com endereços de e-mail em cópia, separados por vírgula.
        bcc (str): String com endereços de e-mail em cópia oculta, separados por vírgula.
        message (str): O corpo da mensagem em HTML.
        attachments (list[dict]): Uma lista de anexos a serem incluídos.
        base_url (str): A URL base da aplicação para rastreamento.
        csv_content (str, optional): O conteúdo de um arquivo CSV, onde cada
            linha é um endereço de e-mail. Defaults to None.
        manual_emails (list[str], optional): Uma lista de endereços de e-mail
            adicionados manualmente. Defaults to None.

    Returns:
        dict: Um dicionário com o status final da operação (`'success'` ou
              `'error'`) e uma mensagem informativa.
    """
    from . import db
    from .models import Campaign, Email
    from app import socketio

    new_campaign = Campaign(subject=subject, message=message)
    db.session.add(new_campaign)
    db.session.commit()

    try:
        all_emails = set()
        if csv_content:
            all_emails.update(line.strip() for line in csv_content.splitlines() if email_regex.match(line.strip()))
        if manual_emails:
            all_emails.update(email.strip() for email in manual_emails if email_regex.match(email.strip()))

        if not all_emails:
            return {'status': 'error', 'message': "Nenhum e-mail válido encontrado."}

        emails_to_send = list(all_emails)
        total_to_send = len(emails_to_send)
        logger.info(f"Iniciando envio de {total_to_send} e-mails para a campanha ID {new_campaign.id}...")

        sent_count = 0
        for email_address in emails_to_send:
            email_id = str(uuid.uuid4())
            new_email = Email(id=email_id, campaign_id=new_campaign.id, recipient=email_address)
            db.session.add(new_email)
            db.session.commit()

            email_data = ([email_address], subject, cc, bcc, message, attachments, email_id)
            result = await send_email_task(email_data, base_url)

            if isinstance(result, dict) and result['status'] == 'success':
                sent_count += 1
                progress_data = {'sent': sent_count, 'total': total_to_send, 'email': email_address}
                socketio.emit('progress', progress_data)
                logger.info(f"Progresso emitido: {progress_data}")
            else:
                error_message = result.get('message', 'Erro desconhecido')
                logger.error(f"Falha ao enviar e-mail para {email_address}: {error_message}")
                socketio.emit('task_error', {'message': f"Falha ao enviar para {email_address}: {error_message}"})
                return {'status': 'error', 'message': f"Falha no envio para {email_address}"}

        logger.info(f"Campanha ID {new_campaign.id} concluída. Enviados {sent_count}/{total_to_send} e-mails.")
        return {'status': 'success', 'message': f"Enviados {sent_count} de {total_to_send} e-mails."}
    except Exception as e:
        logger.error(f"Erro crítico no envio em massa (Campanha ID {new_campaign.id}): {e}", exc_info=True)
        socketio.emit('task_error', {'message': 'Ocorreu um erro interno grave durante o envio.'})
        return {'status': 'error', 'message': str(e)}