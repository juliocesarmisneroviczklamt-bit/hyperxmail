from decouple import config

class Config:
    """
    Configurações centralizadas para a aplicação.
    """
    # Tamanho máximo permitido para anexos (10MB)
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024

    # Limite de e-mails por hora
    EMAILS_PER_HOUR = 500

    # Tempo entre envios de e-mails (em segundos)
    SECONDS_PER_EMAIL = 3600 / EMAILS_PER_HOUR

    # Credenciais e configurações de e-mail
    EMAIL_SENDER = config('EMAIL_SENDER', default='pedidos@biamar.com.br')
    EMAIL_PASSWORD = config('EMAIL_PASSWORD')
    SMTP_SERVER = config('SMTP_SERVER', default='smtp.office365.com')
    SMTP_PORT = config('SMTP_PORT', default=587, cast=int)

    # Token de API para autenticação
    API_TOKEN = config('API_TOKEN', default='pinguinsdemadagascar')

    # Chave secreta para o Flask
    SECRET_KEY = config('SECRET_KEY', default='sua-chave-secreta-aqui')