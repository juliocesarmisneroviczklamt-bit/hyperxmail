import asyncio
import os
import base64
import logging
import aiosmtplib
import tempfile
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import magic
import bleach
import re
from bs4 import BeautifulSoup
from .config import Config

# Configura o logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Regex para validação de e-mails
email_regex = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', re.IGNORECASE)

# Tipos de anexo permitidos
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'application/pdf']

def sanitize_filename(filename):
    """
    Sanitiza um nome de arquivo, removendo caracteres perigosos para prevenir XSS e
    outros ataques. Permite apenas caracteres alfanuméricos, pontos, hífens e underscores.
    """
    return re.sub(r'[^a-zA-Z0-9._-]', '', filename)

async def check_smtp_credentials():
    """
    Verifica se as credenciais SMTP estão corretas de forma assíncrona.

    Returns:
        bool: True se as credenciais estiverem corretas, False caso contrário.
    """
    try:
        # Conecta ao servidor SMTP
        client = aiosmtplib.SMTP(hostname=Config.SMTP_SERVER, port=Config.SMTP_PORT, use_tls=False)
        await client.connect()
        # Inicia o TLS
        await client.starttls()
        # Faz o login
        await client.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        logger.info("Credenciais SMTP verificadas com sucesso.")
        await client.quit()
        return True
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"Erro de autenticação SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar credenciais SMTP: {e}")
        return False

async def send_email_task(email_data, base_url):
    """
    Envia um e-mail assincronamente para um grupo de destinatários.

    Args:
        email_data (tuple): Dados do e-mail (destinatários, assunto, CC, CCO, mensagem, anexos, email_id).
        base_url (str): A URL base da aplicação para rastreamento.

    Returns:
        dict: Resultado do envio com status e mensagem.
    """
    to, subject, cc, bcc, message, attachments, email_id = email_data
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

        # Reescreve os links para rastreamento de cliques
        soup = BeautifulSoup(sanitized_message, 'html.parser')
        for a in soup.find_all('a', href=True):
            original_url = a['href']
            tracking_url = f"{base_url}track/click/{email_id}?url={original_url}"
            a['href'] = tracking_url
        sanitized_message = str(soup)

        # Adiciona o pixel de rastreamento
        tracking_pixel_url = f"{base_url}track/open/{email_id}"
        sanitized_message += f'<img src="{tracking_pixel_url}" width="1" height="1" alt="">'

        # Adiciona o HTML como corpo principal
        html_message = f'<html><body>{sanitized_message}</body></html>'
        html_part = MIMEText(html_message, 'html')
        msg_related.attach(html_part)

        # Processa anexos e vincula imagens ao HTML via cid
        if attachments:
            for i, att in enumerate(attachments):
                # Sanitiza o nome do arquivo para prevenir XSS e outros ataques
                sanitized_filename = sanitize_filename(att['name'])
                if not sanitized_filename:
                    sanitized_filename = "attachment" # Nome padrão se o nome original for totalmente removido

                cid = f'image-{uuid.uuid4()}'  # Gera um Content-ID único
                # Substitui ou adiciona src com cid à tag <img> baseada no alt
                if f'cid:image{i}' in sanitized_message:
                    # Substituir mesmo quando a imagem está dentro de uma tag <a>
                    sanitized_message = sanitized_message.replace(f'cid:image{i}', f'cid:{cid}')
                else:
                    sanitized_message = sanitized_message.replace(
                        f'<img alt="{att["name"]}"',
                        f'<img src="cid:{cid}" alt="{sanitized_filename}"'
                    )
                
                # Atualiza o HTML no corpo
                html_message = f'<html><body>{sanitized_message}</body></html>'
                html_part.set_payload(html_message)

                # Decodifica o base64 e verifica o tamanho
                decoded_data = base64.b64decode(att['data'])
                file_size = len(decoded_data)
                if file_size > Config.MAX_ATTACHMENT_SIZE:
                    logger.error(f"Anexo {sanitized_filename} excede o limite de {Config.MAX_ATTACHMENT_SIZE} bytes.")
                    return {'status': 'error', 'message': f"Anexo {sanitized_filename} excede o limite de 10MB."}
                
                # Verifica o tipo MIME do anexo usando "magic numbers"
                mime_type = magic.from_buffer(decoded_data, mime=True)
                if mime_type not in ALLOWED_MIME_TYPES:
                    logger.error(f"Tipo de anexo não permitido: {mime_type}")
                    return {'status': 'error', 'message': f"Tipo de anexo não permitido: {sanitized_filename}"}
                
                # Salva o arquivo temporário
                # Usar o nome do arquivo sanitizado para determinar o sufixo
                _, suffix = os.path.splitext(sanitized_filename)
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                    tmp_file.write(decoded_data)
                    saved_files.append(tmp_file.name)

                # Anexa como imagem embutida ou anexo normal
                if mime_type.startswith('image/'):
                    with open(tmp_file.name, 'rb') as img_file:
                        img = MIMEImage(img_file.read())
                        img.add_header('Content-ID', f'<{cid}>')
                        img.add_header('Content-Disposition', 'inline', filename=sanitized_filename)
                        msg_related.attach(img)
                else:
                    with open(tmp_file.name, 'rb') as file:
                        part = MIMEApplication(file.read(), Name=sanitized_filename)
                        part['Content-Disposition'] = f'attachment; filename="{sanitized_filename}"'
                        msg.attach(part)

        logger.debug(f"HTML gerado para o e-mail: {html_message}")
        
        # Envia o e-mail de forma assíncrona
        client = aiosmtplib.SMTP(hostname=Config.SMTP_SERVER, port=Config.SMTP_PORT, use_tls=False)
        async with client:
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

async def send_bulk_emails(subject, cc, bcc, message, attachments, base_url, csv_content=None, manual_emails=None):
    from . import db
    from .models import Campaign, Email
    from app import socketio
    # Cria uma nova campanha
    new_campaign = Campaign(subject=subject, message=message)
    db.session.add(new_campaign)
    db.session.commit()

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

        emails_to_send = list(all_emails)
        logger.info(f"Enviando {len(emails_to_send)} e-mails...")

        if not emails_to_send:
            logger.warning("Nenhum e-mail para enviar.")
            return {'status': 'success', 'message': "Nenhum e-mail para enviar."}

        # Envia e-mails sequencialmente para relatar o progresso
        sent_count = 0
        total_to_send = len(emails_to_send)
        for email_address in emails_to_send:
            email_id = str(uuid.uuid4())
            new_email = Email(id=email_id, campaign_id=new_campaign.id, recipient=email_address)
            db.session.add(new_email)
            db.session.commit()

            result = await send_email_task(([email_address], subject, cc, bcc, message, attachments, email_id), base_url)
            if isinstance(result, dict) and result['status'] == 'success':
                sent_count += 1
                # Emite o progresso via WebSocket
                progress_data = {'sent': sent_count, 'total': total_to_send, 'email': email_address}
                socketio.emit('progress', progress_data)
                logger.info(f"Progresso emitido: {progress_data}")
            else:
                # Se um e-mail falhar, podemos decidir parar ou continuar.
                # Por agora, vamos registrar e parar.
                error_message = result.get('message', 'Erro desconhecido')
                logger.error(f"Falha ao enviar e-mail para {email_address}: {error_message}")
                # Emite um erro final e retorna
                socketio.emit('task_error', {'message': f"Falha ao enviar para {email_address}: {error_message}"})
                return {'status': 'error', 'message': f"Falha no envio para {email_address}"}

        return {'status': 'success', 'message': f"Enviados {sent_count} de {total_to_send} e-mails."}
    except Exception as e:
        logger.error(f"Erro no envio em massa: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}